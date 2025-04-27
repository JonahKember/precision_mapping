import os
import shutil
import pandas as pd
import numpy as np
import pandas as pd
import nibabel as nib

from scipy.stats import zscore
from scipy.spatial.distance import dice

def create_func_gii(data, hemi, map_names):
    '''Convert data-arrays to func GIFTI.'''

    darrays = []
    for x, map_name in zip(data, map_names):
        darray = nib.gifti.GiftiDataArray(
            np.array(x, dtype='float32'),
            intent=nib.nifti1.intent_codes['NIFTI_INTENT_NONE'])
        darray.meta = nib.gifti.GiftiMetaData({'Name':map_name})
        darrays.append(darray)

    # Create meta-data.
    if hemi == 'L': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexLeft'})
    if hemi == 'R': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexRight'})

    # Create final GIFTI.
    gifti = nib.GiftiImage(darrays=darrays, meta=meta)
    return gifti


def create_label_gii(data, hemi, map_name):
    '''Convert data-array to label GIFTI with network colors/keys in label-tabel.'''

    # Load template network info.
    df = pd.read_csv('./precision_mapping/data/networks_table.csv')
    label_names = list(df['label'])
    label_indices = list(df['idx'])
    label_colors = [eval(color) for color in list(df['color'])]

    # Create data-array.
    darray = nib.gifti.GiftiDataArray(np.int32(data), intent=nib.nifti1.intent_codes['NIFTI_INTENT_NONE'])
    darray.meta = nib.gifti.GiftiMetaData({'Name': map_name})

    # Create label-tabel.
    labeltable = nib.gifti.GiftiLabelTable()
    for idx, key, (r, g, b) in zip(label_indices,label_names, label_colors):
        label = nib.gifti.GiftiLabel(key=idx, red=r, green=g, blue=b)
        label.label = key
        labeltable.labels.append(label)

    # Create meta-data.
    if hemi == 'L': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexLeft'})
    if hemi == 'R': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexRight'})

    # Combine into GIFTI.
    gifti = nib.GiftiImage(darrays=[darray], labeltable=labeltable, meta=meta)
    return gifti


def run(params):
    '''Perform vertx-wise template matching.'''

    print(f'Running precision-mapping...')

    # Extract relevant parameters.
    hemi = params['hemi']
    output = params['output']
    tmp = params['tmp']

    # Load template networks.
    df = pd.read_csv('./precision_mapping/data/networks_table.csv')
    template = nib.load(f'./precision_mapping/data/networks.32k.{hemi}.label.gii').darrays[0].data
    template_labels = list(df['label'])
    template_indices = list(df['idx'])

    # Create a vertex-by-vertex functional connectivity matrix.
    func_gii = nib.load(params['func'])
    time_series = np.vstack([darray.data for darray in func_gii.darrays])
    time_series_norm = zscore(time_series)
    FC = np.corrcoef(time_series_norm.T)
    FC = np.nan_to_num(FC, 0)

    # Threshold each vertex to top 5% of connections.
    FC[FC <= np.percentile(FC, 95, axis=1, keepdims=True)] = 0

    # Define bad_vertices (those with zero variance: medial-wall and/or dropped signals).
    bad_vertices = np.argwhere(np.isclose(np.var(time_series, axis=0),0)).flatten()

    # Calculate the similarity (1 - dice-distance) of each vertex's FC-profile to each template.
    n_vertices = len(FC)
    similarity = {label: np.zeros([n_vertices]) for label in template_labels}
    for idx, label in zip(template_indices, template_labels):

        print(f'Calculating similarity to {label}...')
        for vertex in range(n_vertices):
            similarity[label][vertex] = 1 - dice(template == idx, FC[vertex, :])

    # Create a [vertex-by-network] similarity matrix, write to .csv.
    net_similarities = np.vstack([similarity[network] for network in template_labels])
    gii = create_func_gii(net_similarities, hemi, template_labels)
    nib.save(gii, f'{output}/network_similarities.{hemi}.func.gii')

    # Find most-similar network for each vertex.
    network_assignments = np.array(template_indices)[np.argmax(net_similarities, axis=0)]
    network_assignments[bad_vertices] = 0

    # Save these undilated network assignments.
    networks_undilated = create_label_gii(network_assignments, hemi, 'undilated')
    nib.save(networks_undilated, f'{output}/networks_undilated.{hemi}.label.gii')

    # Save network-specific giftis to temporary directory for interim processing.
    for idx, label in zip(template_indices, template_labels):
        network_data = network_assignments.copy()
        network_data[network_data != (idx)] = 0
        networks_undilated.darrays[0].data = network_data
        nib.save(networks_undilated, f'{tmp}/{label}.{hemi}.label.gii')

    # Dilate spatially contiguous clusters smaller than the specified threshold into the nearest network.
    filtered_clusters = []
    for idx, label in zip(template_indices, template_labels):

        # Find clusters that are larger than threshold.
        os.system(f'wb_command -metric-find-clusters \
            {params["surf"]} \
            {tmp}/{label}.{hemi}.label.gii 0 \
            {params["dilation_threshold"]} \
            {tmp}/{label}.{hemi}.func.gii'
        )

        # Add [vertex] vector with small clusters removed to 'filtered_clusters'.
        filtered_data = nib.load(f'{tmp}/{label}.{hemi}.func.gii').darrays[0].data
        filtered_data[filtered_data > 0] = (idx)
        filtered_clusters.append(filtered_data)

    # Create label file with all networks.
    filtered_networks = np.sum(np.vstack(filtered_clusters), axis=0)
    gii = create_label_gii(filtered_networks, hemi, 'filtered')
    nib.save(gii, f'{tmp}/filtered_networks.{hemi}.label.gii')

    # Interpolate/dilate removed clusters to nearest network.
    os.system(f'wb_command -metric-dilate \
        {tmp}/filtered_networks.{hemi}.label.gii \
        {params["surf"]} 3000 \
        {tmp}/tmp_dilated.{hemi}.func.gii \
        -nearest'
    )

    # Set bad vertices to 0.
    dilated_data = nib.load(f'{tmp}/tmp_dilated.{hemi}.func.gii').darrays[0].data
    dilated_data[bad_vertices] = 0

    # Save final dilated solution.
    gii = create_label_gii(dilated_data, hemi, 'precision_networks')
    nib.save(gii, f'{output}/networks.{hemi}.label.gii')

    # Delete temporary files.
    shutil.rmtree(tmp)

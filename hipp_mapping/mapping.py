import os
import numpy as np
import nibabel as nib
from scipy.stats import zscore
from importlib import resources


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
    '''Convert data-array to label GIFTI.'''

    # Load template network info.
    label_names = ['anterior','body','posterior']
    label_colors = [
        (0,0.22745098039215686,0.49019607843137253),               # Blue (anterior).
        (0.3058823529411765,0.796078431372549,0.5529411764705883), # Green (body).
        (0.7803921568627451,0.00392156862745098,1)                 # Pink (posterior).
    ]

    # Create data-array.
    darray = nib.gifti.GiftiDataArray(np.int32(data), intent=nib.nifti1.intent_codes['NIFTI_INTENT_NONE'])
    darray.meta = nib.gifti.GiftiMetaData({'Name': map_name})

    # Create label-tabel.
    labeltable = nib.gifti.GiftiLabelTable()
    for idx, key, (r, g, b) in zip(range(len(label_names)), label_names, label_colors):
        label = nib.gifti.GiftiLabel(key=idx, red=r, green=g, blue=b)
        label.label = key
        labeltable.labels.append(label)

    # Create meta-data.
    if hemi == 'L': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexLeft'})
    if hemi == 'R': meta = nib.gifti.GiftiMetaData({'AnatomicalStructurePrimary':'CortexRight'})

    # Combine into GIFTI.
    gifti = nib.GiftiImage(darrays=[darray], labeltable=labeltable, meta=meta)

    return gifti


def nan_corr(x, y):
    '''Calculate Pearson's correlation coefficient between two vectors with NaNs.'''

    valid_mask = ~np.isnan(x) & ~np.isnan(y)
    r = np.corrcoef(x[valid_mask], y[valid_mask])[0, 1]

    return r


def run_mapping(args):

    # Parse input arguments.
    midthickness = args.hipp_midthickness
    surface_dtseries = args.surface_dtseries
    volume_dtseries = args.volume_dtseries
    dilation = args.dilation_threshold
    kernel_fwhm = args.kernel_fwhm
    output = args.output
    hemi = args.hemi

    # Project BOLD time-series from volume to surface via trilinear interpolation and smooth.
    hipp_dtseries_gii = f'{output}/hipp_dtseries.{hemi}.func.gii'
    hipp_dtseries_gii_smoothed = f'{output}/hipp_dtseries_smoothed.{hemi}.func.gii'
    os.system(f'wb_command -volume-to-surface-mapping {volume_dtseries} {midthickness} {hipp_dtseries_gii} -trilinear')
    os.system(f'wb_command -metric-smoothing {midthickness} {hipp_dtseries_gii} {kernel_fwhm} {hipp_dtseries_gii_smoothed} -fwhm')

    # Correlate hippocampal-vertex and cortical-vertex BOLD signals.
    gii = nib.load(hipp_dtseries_gii_smoothed)
    hipp_time_series = np.array([darray.data for darray in gii.darrays])
    hipp_time_series = zscore(hipp_time_series)

    gii = nib.load(surface_dtseries)
    cortical_time_series = np.array([darray.data for darray in gii.darrays])
    cortical_time_series = zscore(cortical_time_series)

    n_TRs = hipp_time_series.shape[0]
    hipp_FC = hipp_time_series.T @ cortical_time_series / (n_TRs - 1)
    np.save(f'{output}/hipp_cortex_FC.{hemi}.npy', hipp_FC)

    # Assign each vertex to a system based on its FC profile.
    template = resources.files('hipp_mapping.data') / f'template.{hemi}.shape.gii'

    FC_templates = np.array([darray.data for darray in nib.load(template).darrays])
    n_vertices = hipp_FC.shape[0]
    n_templates = FC_templates.shape[0]

    vertex_r = np.zeros([n_templates,n_vertices])
    for vertex in range(n_vertices):
        vertex_r[:,vertex] = [nan_corr(hipp_FC[vertex,:], FC_templates[n,:]) for n in range(n_templates)]

    vertex_n = np.argmax(vertex_r, axis=0)

    gii = create_func_gii(list(vertex_r), hemi=hemi, map_names=['anterior','body','posterior'])
    nib.save(gii, f'{output}/hipp_system_corrs.{hemi}.func.gii')

    # Clean solutions through spatial dilation.
    for n in range(n_templates):
        gifti = create_func_gii([np.int32(np.array(vertex_n) == n)], hemi, 'tmp')
        nib.save(gifti, f'{output}/tmp/tmp_{n}.func.gii')
        os.system(f'wb_command -metric-find-clusters {midthickness} {output}/tmp/tmp_{n}.func.gii 0 {dilation} {output}/tmp/tmp_{n}_filtered.func.gii')

    cleaned_data = np.zeros(n_vertices)
    for n in range(n_templates):
        cleaned_cluster = nib.load(f'{output}/tmp/tmp_{n}_filtered.func.gii').darrays[0].data
        cleaned_data[cleaned_cluster > 0] = n + 1

    gii = create_func_gii([np.int32(cleaned_data)], hemi=hemi, map_names='cleaned')
    nib.save(gii, f'{output}/tmp/tmp_cleaned_data.func.gii')

    tmp_gii = f'{output}/tmp/tmp_hipp_systems.{hemi}.func.gii'
    os.system(f'wb_command -metric-dilate {output}/tmp/tmp_cleaned_data.func.gii {midthickness} 3000 {tmp_gii} -nearest')

    hipp_systems = nib.load(tmp_gii).darrays[0].data - 1
    gii = create_label_gii(hipp_systems, hemi, map_name='systems')
    nib.save(gii, f'{output}/hipp_systems.{hemi}.label.gii')

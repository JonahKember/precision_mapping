import numpy as np
import pandas as pd
import nibabel as nib

from feature_extraction import utils
from cortex_mapping import mapping


def get_network_connectivity(args):
    '''Calculate the mean network-wise connectivity of each spatial cluster.'''

    #  Set-up
    func = args.func
    hemi = args.hemi
    output = args.output
    tmp = f'{args.output}tmp'
    networks = args.networks

    network_indices, network_labels, _ = mapping.get_template_info()
    clusters = nib.load(f'{tmp}/clusters.{hemi}.func.gii')
    time_series = utils.get_time_series(func)
    network_data = nib.load(networks).darrays[0].data

    # Correlate each cluster's mean BOLD time-series with the mean network time-series.
    network_time_series = [time_series[:, network_data == idx].mean(axis=1) for idx in network_indices]

    network_corrs = []
    for darray in clusters.darrays:
        cluster_indices = np.argwhere(darray.data).flatten()
        cluster_time_series = time_series[:, cluster_indices].mean(axis=1)

        corrs = np.array([np.corrcoef(cluster_time_series, xs)[0,1] for xs in network_time_series])
        network_corrs.append(corrs)

    df = pd.read_csv(f'{output}/features_{hemi}.csv')
    feature_names = [f'{net}__connectivity' for net in network_labels]
    df[feature_names] = np.array(network_corrs)
    df.to_csv(f'{output}/features_{hemi}.csv', index=False)

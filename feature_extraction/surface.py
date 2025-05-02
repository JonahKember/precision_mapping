import subprocess
import numpy as np
import nibabel as nib

from precision_mapping import mapping
from feature_extraction import utils


def get_clusters(networks, surf, hemi, tmp):
    '''
    Identify spatial clusters and their border vertices.

    Input:
    networks: path to networks label GIFTI.
    surf: path to midthickness surface GIFTI.
    hemi: current hemisphere, string ('L','R')
    tmp: temporary directory.

    Output:
    cluters_gii: GIFTI, each spatial cluster is saved as a boolean darray.
    borders_gii: GIFTI, border vertices of each spatial cluster are saved as a boolean darray.
    '''

    network_indices, network_labels = utils.get_template_info()

    # Separate networks into separate darrays.
    networks_bool = [nib.load(networks).darrays[0].data == network_idx for network_idx in network_indices]
    network_gii = mapping.create_func_gii(networks_bool, hemi=hemi, map_names=network_labels)
    nib.save(network_gii, f'{tmp}/networks_separated.{hemi}.func.gii')

    # Identify clusters for each network.
    subprocess.run([
        f'wb_command', '-metric-find-clusters',
        f'{surf}',                                    # <surface> - the surface to compute on
        f'{tmp}/networks_separated.{hemi}.func.gii',  # <metric-in> - the input metric
        '0',                                          # <value-threshold> - threshold for data values
        '0',                                          # <minimum-area> - threshold for cluster area, in mm^2
        f'{tmp}/clusters.{hemi}.func.gii'             # <metric-out> - output - the output metric
    ])

    # Create single darray for each cluster.
    cluster_darrays = nib.load(f'{tmp}/clusters.{hemi}.func.gii').darrays

    clusters_bool = []
    for darray in cluster_darrays:
        cluster_indices = set(darray.data)
        cluster_indices.remove(0)
        clusters_bool.append([darray.data == idx for idx in cluster_indices])

    cluster_bool = np.vstack(clusters_bool)
    map_names=[f'{idx}' for idx in range(cluster_bool.shape[1])]

    # Write clusters to temporary directory.
    clusters_gii = mapping.create_func_gii(cluster_bool, hemi, map_names=map_names)
    nib.save(clusters_gii, f'{tmp}/clusters.{hemi}.func.gii')

    # Find border vertices of clusters.
    subprocess.run([
        f'wb_command', '-metric-rois-to-border',
        f'{surf}',                                # <surface> - the surface to use for neighbor information
        f'{tmp}/clusters.{hemi}.func.gii',        # <metric> - the input metric containing ROIs
        f'network_clusters',                      # <class-name> - the name to use for the class of the output borders
        f'{tmp}/borders.{hemi}.border',           # <border-out> - output - the output border file
    ])

    subprocess.run([
        f'wb_command', '-border-to-vertices',
        f'{surf}',                               # <surface> - the surface to compute on
        f'{tmp}/borders.{hemi}.border',          # <border-file> - the border file
        f'{tmp}/borders.{hemi}.func.gii'         # <metric-out> - output - the output metric file
    ])

    borders_gii = nib.load(f'{tmp}/borders.{hemi}.func.gii')

    return clusters_gii, borders_gii

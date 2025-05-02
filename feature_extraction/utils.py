import numpy as np
import pandas as pd
import nibabel as nib

from scipy.stats import zscore
from scipy.spatial import cKDTree


def get_template_info():
    '''Get indices and labels of the template network.'''

    network_tbl = pd.read_csv('./precision_mapping/data/networks_table.csv')
    network_indices = list(network_tbl['idx'])
    network_labels = list(network_tbl['label'])

    return network_indices, network_labels


def get_cohens_d(data_1, data_2):
    '''Calculate Cohen's d effect-size difference (absolute value).'''

    n1 = len(data_1)
    n2 = len(data_2)

    var_1 = np.var(data_1, ddof=1)
    var_2 = np.var(data_2, ddof=1)

    pooled_sd = np.sqrt(((n1 - 1)*var_1 + (n2 - 1)*var_2) / (n1 + n2 - 2))
    cohens_d = np.abs((np.mean(data_1) - np.mean(data_2)) / pooled_sd)

    return cohens_d


def get_time_series(func):
    '''Get z-scored [sample, vertex] BOLD time-series array.'''

    func_gii = nib.load(func)
    time_series = np.vstack([darray.data for darray in func_gii.darrays])
    time_series = zscore(time_series)

    return time_series


def get_surf_coords(surf):
    '''Get [x,y,z] coordinates of surface vertices.'''

    surf_gii = nib.load(surf)
    coords = surf_gii.darrays[0].data

    return coords


def get_kdtree(surf):
    '''Get scipy-spatial KDTree from surface-coordinates.'''

    coords = get_surf_coords(surf)
    tree = cKDTree(coords)

    return tree

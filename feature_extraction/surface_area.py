import subprocess
import numpy as np
import pandas as pd
import nibabel as nib

def get_surface_area(params):

    #  Set-up
    surf = params['surf']
    hemi = params['hemi']
    output = params['output']
    tmp = params['tmp']

    # Get cluster surface-areas
    subprocess.run([
        f'wb_command','-surface-vertex-areas',f'{surf}',f'{tmp}/surface_area.{hemi}.func.gii'
    ])

    surf_area = nib.load(f'{tmp}/surface_area.{hemi}.func.gii').darrays[0].data
    clusters = nib.load(f'{tmp}/clusters.{hemi}.func.gii')

    cluster_surf_area = [np.sum(surf_area[np.argwhere(darray.data)]) for darray in clusters.darrays]

    # Add surface-areas to dataframe and save.
    features_df = pd.read_csv(f'{output}/features_{hemi}.csv')
    surf_area_df = pd.DataFrame(data=cluster_surf_area, columns=['surface_area'])

    df = pd.concat([features_df, surf_area_df], axis=1)
    df.to_csv(f'{output}/features_{hemi}.csv', index=False)


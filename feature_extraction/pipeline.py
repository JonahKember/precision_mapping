from feature_extraction import clusters, utils, surface_area, connectivity, sharpness

def extract_features(args):

    # Prepare clusters and dataframe to hold results.
    clusters.get_clusters(args)
    utils.initialize_dataframe(args)

    # Extract features.
    surface_area.get_surface_area(args)
    connectivity.get_network_connectivity(args)
    sharpness.get_boundary_sharpness(args)

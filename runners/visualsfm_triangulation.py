import os, sys
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import core.utils as utils

import limap.base as _base
import limap.pointsfm as _psfm
import limap.util.io as limapio
import limap.runners

def run_visualsfm_triangulation(cfg, vsfm_path, nvm_file="reconstruction.nvm"):
    '''
    Run triangulation from VisualSfM input
    '''
    metainfos_filename = "infos_visualsfm.npy"
    output_dir = "tmp" if cfg["output_dir"] is None else cfg["output_dir"]
    limapio.check_makedirs(output_dir)
    if cfg["skip_exists"] and os.path.exists(os.path.join(output_dir, metainfos_filename)):
        cfg["info_path"] = os.path.join(output_dir, metainfos_filename)
    if cfg["info_path"] is None:
        imagecols, neighbors, ranges = _psfm.read_infos_visualsfm(cfg["sfm"], vsfm_path, nvm_file=nvm_file, n_neighbors=cfg["n_neighbors"])
        with open(os.path.join(output_dir, metainfos_filename), 'wb') as f:
            np.savez(f, imagecols_np=imagecols.as_dict(), neighbors=neighbors, ranges=ranges)
    else:
        with open(cfg["info_path"], 'rb') as f:
            data = np.load(f, allow_pickle=True)
            imagecols_np, neighbors, ranges = data["imagecols_np"].item(), data["neighbors"], data["ranges"]
            imagecols = _base.ImageCollection(imagecols_np)

    # run triangulation
    linetracks = limap.runners.line_triangulation(cfg, imagecols, neighbors=neighbors, ranges=ranges)
    return linetracks

def parse_config():
    import argparse
    arg_parser = argparse.ArgumentParser(description='triangulate 3d lines from bundler')
    arg_parser.add_argument('-c', '--config_file', type=str, default='cfgs/triangulation/default.yaml', help='config file')
    arg_parser.add_argument('--default_config_file', type=str, default='cfgs/triangulation/default.yaml', help='default config file')
    arg_parser.add_argument('-a', '--vsfm_path', type=str, required=True, help='visualsfm path')
    arg_parser.add_argument('--nvm_file', type=str, default='reconstruction.nvm', help='nvm filename')
    arg_parser.add_argument('--max_image_dim', type=int, default=None, help='max image dim')
    arg_parser.add_argument('--info_path', type=str, default=None, help='load precomputed info')

    args, unknown = arg_parser.parse_known_args()
    cfg = utils.load_config(args.config_file, default_path=args.default_config_file)
    shortcuts = dict()
    shortcuts['-nv'] = '--n_visible_views'
    shortcuts['-nn'] = '--n_neighbors'
    cfg = utils.update_config(cfg, unknown, shortcuts)
    cfg["vsfm_path"] = args.vsfm_path
    cfg["nvm_file"] = args.nvm_file
    cfg["info_path"] = args.info_path
    if ("max_image_dim" not in cfg.keys()) or args.max_image_dim is not None:
        cfg["max_image_dim"] = args.max_image_dim
    return cfg

def main():
    cfg = parse_config()
    run_visualsfm_triangulation(cfg, cfg["vsfm_path"], nvm_file=cfg["nvm_file"])

if __name__ == '__main__':
    main()


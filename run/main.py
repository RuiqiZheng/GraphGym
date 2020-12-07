import os
import random
import numpy as np
import torch
import logging
import pdb

from graphgym.cmd_args import parse_args
from graphgym.config import (cfg, assert_cfg, dump_cfg,
                             update_out_dir, get_parent_dir)
from graphgym.loader import create_dataset, create_loader
from graphgym.logger import setup_printing, create_logger
from graphgym.optimizer import create_optimizer, create_scheduler
from graphgym.model_builder import create_model
from graphgym.train import train
from graphgym.utils.agg_runs import agg_runs
from graphgym.utils.comp_budget import params_count
from graphgym.utils.device import auto_select_device
from graphgym.contrib.train import *
from graphgym.register import train_dict


def train_one_solution(dataset='Cora', dim_inner=256, layers_mp=8, layers_pre_mp=1, layers_post_mp=1,
                       layer_type='generalconv', stage_type='stack', batchnorm='True', act='prelu', dropout=0.6,
                       agg='add', device='auto'):
    # Load cmd line args
    # args = parse_args()
    # Repeat for different random seeds

    # Load config file
    cfg.merge_from_file('configs/example.yaml')
    # cfg.merge_from_list(args.opts)
    assert_cfg(cfg)
    # Set Pytorch environment
    torch.set_num_threads(cfg.num_threads)
    out_dir_parent = cfg.out_dir
    cfg.seed = 2

    cfg.dataset.name = dataset
    cfg.gnn.layers_mp = layers_mp
    cfg.gnn.layers_pre_mp = layers_pre_mp
    cfg.gnn.layer_type = layer_type
    cfg.gnn.stage_type = stage_type
    cfg.gnn.batchnorm = batchnorm
    cfg.gnn.act = act
    cfg.gnn.dropout = dropout
    cfg.gnn.agg = agg
    cfg.gnn.layers_post_mp = layers_post_mp
    cfg.device = device
    cfg.gnn.dim_inner = dim_inner

    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)
    # update_out_dir(out_dir_parent, args.cfg_file)
    dump_cfg(cfg)
    setup_printing()
    auto_select_device()
    # Set learning environment
    datasets = create_dataset()
    loaders = create_loader(datasets)
    meters = create_logger(datasets, loaders)
    model = create_model(datasets)
    optimizer = create_optimizer(model.parameters())
    scheduler = create_scheduler(optimizer)
    # Print model info
    logging.info(model)
    logging.info(cfg)
    cfg.params = params_count(model)
    logging.info('Num parameters: {}'.format(cfg.params))
    # Start training
    if cfg.train.mode == 'standard':
        best_val_accuracy = train(meters, loaders, model, optimizer, scheduler)
    else:
        train_dict[cfg.train.mode](
            meters, loaders, model, optimizer, scheduler)
    # # Aggregate results from different seeds
    # agg_runs(get_parent_dir(out_dir_parent, args.cfg_file), cfg.metric_best)
    # # When being launched in batch mode, mark a yaml as done
    # if args.mark_done:
    #     os.rename(args.cfg_file, '{}_done'.format(args.cfg_file))
    return best_val_accuracy


if __name__ == '__main__':
    train_one_solution('Cora', dim_inner=256, layers_mp=2)

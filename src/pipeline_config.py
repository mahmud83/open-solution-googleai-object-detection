import os

import neptune
from attrdict import AttrDict
from .utils import read_params, parameter_eval, get_class_mappings

ctx = neptune.Context()
params = read_params(ctx)

ID_COLUMN = 'ImageID'
LABEL_COLUMN = 'LabelName'
SEED = 1234
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

DESIRED_CLASS_SUBSET = parameter_eval(params.desired_class_subset)
N_SUB_CLASSES = len(DESIRED_CLASS_SUBSET)

ASPECT_RATIOS = parameter_eval(params.aspect_ratios)
SCALE_RATIOS = parameter_eval(params.scale_ratios)

CODES2NAMES, NAMES2CODES = get_class_mappings(mappings_file=params.class_mappings_filepath)

GLOBAL_CONFIG = {'exp_root': params.experiment_dir,
                 'load_in_memory': params.load_in_memory,
                 'num_workers': params.num_workers,
                 'num_classes': N_SUB_CLASSES if N_SUB_CLASSES else params.num_classes,
                 'batch_size_train': params.batch_size_train,
                 'batch_size_inference': params.batch_size_inference,
                 'loader_mode': params.loader_mode,
                 'stream_mode': params.stream_mode,
                 'max_annotation_per_class': params.max_annotation_per_class,
                 'use_suppression': params.use_suppression,
                 }

SOLUTION_CONFIG = AttrDict({
    'env': {'cache_dirpath': params.experiment_dir},
    'execution': GLOBAL_CONFIG,

    'label_encoder': {'colname': LABEL_COLUMN
                      },
    'loader': {'dataset_params': {'images_dir': None,
                                  'short_dim': params.short_dim,
                                  'long_dim': params.long_dim,
                                  'fixed_h': params.fixed_h,
                                  'fixed_w': params.fixed_w,
                                  'sampler_name': params.sampler_name,
                                  'pad_method': params.pad_method,
                                  'sample_size': params.training_sample_size,
                                  'valid_sample_size': params.validation_sample_size,
                                  'even_class_sampling': params.even_class_sampling,
                                  'use_suppression': params.use_suppression,
                                  'data_encoder': {'aspect_ratios': ASPECT_RATIOS,
                                                   'scale_ratios': SCALE_RATIOS,
                                                   'num_anchors': len(ASPECT_RATIOS) * len(SCALE_RATIOS)}
                                  },
               'loader_params': {'training': {'batch_size': params.batch_size_train,
                                              'shuffle': False,
                                              'num_workers': params.num_workers,
                                              'pin_memory': params.pin_memory
                                              },
                                 'inference': {'batch_size': params.batch_size_inference,
                                               'shuffle': False,
                                               'num_workers': params.num_workers,
                                               'pin_memory': params.pin_memory
                                               },
                                 },
               },

    'retinanet': {
        'architecture_config': {'model_params': {'encoder_depth': params.encoder_depth,
                                                 'num_classes': N_SUB_CLASSES if N_SUB_CLASSES else params.num_classes,
                                                 # we change the model output size if subclasses used
                                                 # fallback to config file
                                                 'num_anchors': len(ASPECT_RATIOS) * len(SCALE_RATIOS),
                                                 'pretrained_encoder': params.pretrained_encoder
                                                 },
                                'optimizer_params': {'lr': params.lr,
                                                     },
                                'regularizer_params': {'regularize': True,
                                                       'weight_decay_conv2d': params.l2_reg_conv,
                                                       },
                                'weights_init': {'function': 'he',
                                                 'pi': params.pi
                                                 }
                                },
        'training_config': {'epochs': params.epochs_nr,
                            },
        'callbacks_config': {
            'model_checkpoint': {
                'filepath': os.path.join(GLOBAL_CONFIG['exp_root'], 'checkpoints', 'retinanet', 'best.torch'),
                'epoch_every': 1,
                # 'minimize': not params.validate_with_map
            },
            'exp_lr_scheduler': {'gamma': params.gamma,
                                 'epoch_every': 1},
            'plateau_lr_scheduler': {'lr_factor': params.lr_factor,
                                     'lr_patience': params.lr_patience,
                                     'epoch_every': 1},
            'training_monitor': {'batch_every': 1,
                                 'epoch_every': 1},
            'experiment_timing': {'batch_every': 10,
                                  'epoch_every': 1},
            'validation_monitor': {
                'epoch_every': 1,
                # 'data_dir': params.train_imgs_dir,
                # 'validate_with_map': params.validate_with_map,
                # 'small_annotations_size': params.small_annotations_size,
            },
            'neptune_monitor': {'model_name': 'unet',
                                # 'image_nr': 16,
                                # 'image_resize': 0.2,
                                # 'outputs_to_plot': params.unet_outputs_to_plot
                                },
            'early_stopping': {'patience': params.patience,
                               # 'minimize': not params.validate_with_map
                               },
        },
    },
    'postprocessing': {
        'data_decoder': {
            'short_dim': params.short_dim,
            'long_dim': params.long_dim,
            'fixed_h': params.fixed_h,
            'fixed_w': params.fixed_w,
            'sampler_name': params.sampler_name,
            'num_threads': params.num_threads,
            'aspect_ratios': ASPECT_RATIOS,
            'scale_ratios': SCALE_RATIOS,
            'num_anchors': len(ASPECT_RATIOS) * len(SCALE_RATIOS),
            'cls_thrs': params.classification_threshold,
            'nms_thrs': params.nms_threshold
        }
    },
})

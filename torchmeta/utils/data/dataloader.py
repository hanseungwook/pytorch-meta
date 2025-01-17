from collections import OrderedDict

from torch.utils.data import DataLoader
from torch.utils.data.dataloader import default_collate
from torch.utils.data.dataset import Dataset as TorchDataset

from torchmeta.utils.data.dataset import CombinationMetaDataset
from torchmeta.utils.data.sampler import (CombinationSequentialSampler,
                                          CombinationRandomSampler)

import numpy as np

class BatchMetaCollate(object):

    def __init__(self, collate_fn, idx=False):
        super().__init__()
        self.collate_fn = collate_fn
        self.idx = idx

    def collate_task(self, task, task_idx=None):
        if isinstance(task, TorchDataset):
            if task_idx is not None:
                return self.collate_fn([[*task[idx], np.asarray([task_idx])] for idx in range(len(task))])
            else:
                return self.collate_fn([task[idx] for idx in range(len(task))])
        elif isinstance(task, OrderedDict):
            return OrderedDict([(key, self.collate_task(subtask))
                for (key, subtask) in task.items()])
        else:
            raise NotImplementedError()

    def __call__(self, batch):
        if not self.idx:
            return self.collate_fn([self.collate_task(task) for task in batch])
        else:
            return self.collate_fn([self.collate_task(task, idx) for task, idx in batch])

def no_collate(batch):
    return batch

class MetaDataLoader(DataLoader):
    def __init__(self, dataset, batch_size=1, shuffle=True, sampler=None,
                 batch_sampler=None, num_workers=0, collate_fn=None,
                 pin_memory=False, drop_last=False, timeout=0,
                 worker_init_fn=None):
        if collate_fn is None:
            collate_fn = no_collate
        
        if isinstance(dataset, CombinationMetaDataset) and (sampler is None):
            if shuffle:
                sampler = CombinationRandomSampler(dataset)
            else:
                sampler = CombinationSequentialSampler(dataset)
            shuffle = False

        super(MetaDataLoader, self).__init__(dataset, batch_size=batch_size,
            shuffle=shuffle, sampler=sampler, batch_sampler=batch_sampler,
            num_workers=num_workers, collate_fn=collate_fn,
            pin_memory=pin_memory, drop_last=drop_last, timeout=timeout,
            worker_init_fn=worker_init_fn)


class BatchMetaDataLoader(MetaDataLoader):
    def __init__(self, dataset, batch_size=1, shuffle=True, sampler=None, num_workers=0,
                 pin_memory=False, drop_last=False, timeout=0, worker_init_fn=None):
        collate_fn = BatchMetaCollate(default_collate)

        super(BatchMetaDataLoader, self).__init__(dataset,
            batch_size=batch_size, shuffle=shuffle, sampler=sampler,
            batch_sampler=None, num_workers=num_workers,
            collate_fn=collate_fn, pin_memory=pin_memory, drop_last=drop_last,
            timeout=timeout, worker_init_fn=worker_init_fn)

class BatchMetaIdxDataLoader(MetaDataLoader):
    def __init__(self, dataset, batch_size=1, shuffle=True, sampler=None, num_workers=0,
                 pin_memory=False, drop_last=False, timeout=0, worker_init_fn=None):
        collate_fn = BatchMetaCollate(default_collate, idx=True)

        super(BatchMetaIdxDataLoader, self).__init__(dataset,
            batch_size=batch_size, shuffle=shuffle, sampler=sampler,
            batch_sampler=None, num_workers=num_workers,
            collate_fn=collate_fn, pin_memory=pin_memory, drop_last=drop_last,
            timeout=timeout, worker_init_fn=worker_init_fn)

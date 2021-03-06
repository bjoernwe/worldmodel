import numpy as np
import weakref

import tree_structure


class WorldmodelTree(tree_structure.Tree):
    
    def __init__(self, partitioning):
        super(WorldmodelTree, self).__init__()

        # references        
        self._partitioning = self._get_weakref_proxy(partitioning)
        self._active_action = partitioning.active_action
        self.model = self._get_weakref_proxy(partitioning.model)
        
        # indices of data belonging to this node
        self.data_refs = np.empty(0, dtype=int)
        
        # if node is split, parameters are stored here
        self._split_params = None
        
        # a split result that was not (yet) applied
        self._cached_split_params = None
        return
    
    
    def _get_weakref_proxy(self, ref):
        if type(ref) in weakref.ProxyTypes:
            return ref
        return weakref.proxy(ref)
        
        
    def _calc_test_params(self, active_action, fast_partition=False):
        """
        Initializes the parameters that split the node in two halves and returns
        them.
        """
        raise NotImplementedError("Use subclass like WorldmodelSpectral instead.")


    def _test(self, x, params):
        """
        Tests to which child the data point x belongs. Parameters are the ones
        calculated by calc_test_params().
        """
        raise NotImplementedError("Use subclass like WorldmodelSpectral instead.")
    

    def classify(self, x):
        """
        Returns the state that x belongs to according to the current model. If
        x is a matrix, a list is returned containing a integer state for every
        row.
        """
        
        assert self.get_root() is self
        assert x.ndim == 2
        
        N, _ = x.shape
        labels = np.zeros(N, dtype=int)
        leaves = self.get_leaves()
        node_indices = dict(zip(leaves, [leaf.get_leaf_index() for leaf in leaves]))
        
        for i, dat in enumerate(x):
            
            node = self
            while not node.is_leaf():
                child_index = node._test(dat, params=node._split_params._test_params)
                node = node._children[child_index]
                
            labels[i] = node_indices[node]

        return labels
            
            
    def get_number_of_samples(self):
        return len(self.data_refs)
            
            
    def get_data(self):
        """
        Returns the data belonging to the node. If the node isn't a leaf, the
        data of sub-nodes is returned.
        """
        
        model = self.model
        model_data = model.data
        dat_refs = sorted(self.get_data_refs())
        N = len(dat_refs)
        D = model.get_input_dim()
        
        if N == 0:
            return None
        
        data = np.empty((N, D))
        for i, ref in enumerate(dat_refs):
            data[i] = model_data[ref]
            
        return data 
    
    
    #@profile
    def split(self, split_params):
        """
        Applies a split.
        """
        
        assert self.is_leaf()
        self._split_params = split_params
        
        # copy labels and transitions to model
        leaf_index = self.get_leaf_index()
        assert len(self.data_refs) == np.count_nonzero(self._partitioning.labels == leaf_index)
        self._partitioning.labels = split_params.get_new_labels()
        self._partitioning.transitions = split_params.get_new_transition_matrices()
        
        # copy new references to children
        new_dat_refs = split_params.get_new_data_refs()
        assert len(self.data_refs) == len(new_dat_refs[0]) + len(new_dat_refs[1])
        child_1, child_2 = super(WorldmodelTree, self).split(partitioning=self._partitioning)
        child_1.data_refs = new_dat_refs[0]
        child_2.data_refs = new_dat_refs[1]
        
        # 
        assert len(child_1.data_refs) == np.count_nonzero(self._partitioning.labels == leaf_index)
        assert len(child_2.data_refs) == np.count_nonzero(self._partitioning.labels == leaf_index+1)
        
        #assert False not in [model.partitionings[action].labels[ref]==leaf_index for ref in child_1.data_refs]
        #assert False not in [model.partitionings[action].labels[ref]==leaf_index+1 for ref in child_2.data_refs]
        
        # free some memory
        self.data_refs = None
        return child_1, child_2
    

    def get_data_refs(self):
        """
        Returns a list of data references (i.e. indices for root.data) 
        belonging to the node. If the node isn't a leaf, the data of sub-nodes 
        is returned.
        """

        if self.is_leaf():
            return self.data_refs

        # else        
        data_refs = np.empty(0, dtype=int)
        for child in self._children:
            data_refs = np.hstack([data_refs, child.get_data_refs()])
        
        data_refs.sort()
        return data_refs


    def get_transition_refs(self, heading_in=False, inside=True, heading_out=False):
        """
        Finds all transitions that start, end or happen strictly inside the 
        node. The result is given as two lists of references. One for the start 
        and one for the end of the transition.
        """
        
        refs_1 = self.get_data_refs()
        refs_0 = refs_1 - 1
        N = self.model.get_number_of_samples()
        result = np.empty(0, dtype=int)
        
        if heading_in:
            # [ref-1 for ref in refs if (ref-1 not in refs) and (ref-1 >= 0)]
            assert False
            refs_array_in = np.setdiff1d(refs_0, refs_1, assume_unique=True)
            refs_array_in.difference_update([-1])
            assert set(refs_array_in) == set([ref-1 for ref in refs_1 if (ref-1 not in refs_1) and (ref-1 >= 0)])
            result = np.union1d(result, refs_array_in)
            
        if inside:
            # [ref for ref in refs if (ref+1 in refs)]
            mask = np.in1d(refs_1, refs_0, assume_unique=True)
            refs_array_inside = refs_1[mask]
            #assert set(refs_array_inside) == set([ref for ref in refs if (ref+1 in refs)])
            result = np.union1d(result, refs_array_inside)

        if heading_out:
            # [ref for ref in refs if (ref+1 not in refs) and (ref+1 < N)]
            refs_array_out = np.setdiff1d(refs_1, refs_0, assume_unique=True)
            refs_array_out = np.setdiff1d(refs_array_out, np.array([N-1], dtype=int))
            assert set(refs_array_out) == set([ref for ref in refs_1 if (ref+1 not in refs_1) and (ref+1 < N)])
            result = np.union1d(result, refs_array_out)
            
        return result
        
        
    def get_transition_refs_for_action(self, action, heading_in=False, inside=True, heading_out=False):
        refs = self.get_transition_refs(heading_in=heading_in, inside=inside, heading_out=heading_out)
        actions = self.model.actions[refs]
        mask = (actions == action)
        return refs[mask]
    
    
#     def _reached_number_of_active_and_inactive_samples(self, number, active_action):
#         """
#         Calculates whether for the active_action and all other actions a certain
#         number of samples is reached.
#         """
#         refs_1, _ = self.get_transition_refs(heading_in=False, inside=True, heading_out=False)
#         actions = [self.model.actions[ref] for ref in refs_1]
#         
#         n_actions = len(self.model.get_known_actions())
#         n_samples = len(refs_1)
#         n_samples_active = actions.count(active_action)
#         n_samples_inactive = n_samples - n_samples_active
#         
#         return (n_samples_active >= number) and (n_actions == 1 or n_samples_inactive >= number)
        
        

if __name__ == '__main__':
    pass

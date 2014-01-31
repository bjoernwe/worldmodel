import numpy as np
import weakref

from matplotlib import pyplot

import split_params


class Partitioning(object):
    
    def __init__(self, model, active_action):#, tree, labels, transitions):
        self.model = weakref.proxy(model)
        self.active_action = active_action
        #self.tree = tree
        #self.labels = labels
        #self.transitions = transitions
        
        N = model.get_number_of_samples()
        self.labels = np.zeros(N, dtype=int)
        self.tree = self.model._tree_class(partitioning=self)#model=self, active_action=active_action)
        self.transitions = {}
        for action in self.model.get_known_actions():
            self.transitions[action] = np.ones((1, 1), dtype=int) * np.count_nonzero(self.model.actions == action)


    def classify(self, data):
        """
        Returns the state(s) that the data belongs to according to the current 
        model.
        """
        return self.tree.classify(data)
    

    def get_merged_transition_matrices(self):
        """
        Merges all transition matrices.
        """
        
        K = self.tree.get_number_of_leaves()
        P = np.zeros((K, K), dtype=int)
        
        for a in self.model.get_known_actions():
            P += self.transitions[a]

        assert np.sum(P) == self.model.get_number_of_samples() - 1
        return P


    def calc_best_split(self):
        """
        Calculates the gain for each state and returns a split-object for the
        best one
        """
        
        if self.model.data is None:
            return None
                
        best_split = None

        for leaf in self.tree.get_leaves():
            
            if leaf._cached_split_params is None:
                leaf._cached_split_params = split_params.SplitParamsLocalGain(node=leaf)
                
            split = leaf._cached_split_params
            split.update()
                
            # TODO: find a way to mark split as invalid (for instance test_params failed)
            if split is not None:
                if best_split is None or split.get_gain() >= best_split.get_gain():
                    best_split = split
                
        return best_split


    def plot_data_colored_for_state(self, show_plot=True):
        """
        Plots all the data that is stored in the tree with color and shape
        according to the learned state.
        """
        
        # fancy shapes and colors
        symbols = ['o', '^', 'd', 's', '*']
        colormap = pyplot.cm.get_cmap('prism')
        pyplot.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.98, 7)])
        
        # data for the different classes
        leaves = self.tree.get_leaves()
        for i, leaf in enumerate(leaves):
            data = leaf.get_data()
            pyplot.plot(data[:,0], data[:,1], symbols[i%len(symbols)])
                
        if show_plot:
            pyplot.show()
            
        return
    


if __name__ == '__main__':
    pass

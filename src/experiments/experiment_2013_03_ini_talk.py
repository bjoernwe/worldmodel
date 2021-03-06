"""
Generates the plots shown at my INI talk.
"""

from matplotlib import pyplot

import worldmodel
from experiment_2013_02_noisy_dim import NoisyDimData
from experiment_2013_03_random_walk_2d import RandomWalk2DData
from experiment_2013_03_random_walk_swissroll import RandomSwissRollData

            
if __name__ == '__main__':

    data_generators = [RandomSwissRollData,
                       NoisyDimData,
                       RandomWalk2DData]
    plot_ranges = [[-1, 1], [0, 1], [0, 1]]
    data_sizes = [4000, 4000, 4000]

    for i, generator in enumerate(data_generators):
        
        # train model
        data = generator(n=data_sizes[i], seed=1)
        model = worldmodel.WorldModel(method='spectral')
        model.add_data(data=data.data, actions=data.actions)
        model.learn(min_gain=0.02)
        
        # plot data and result
        pyplot.figure()
        model.plot_state_borders(show_plot=False, resolution=100)
        pyplot.xlabel('feature 1')
        pyplot.ylabel('feature 2')
        #if i == 0:
        pyplot.figure()
        model.plot_data(color='none', show_plot=False)
        pyplot.xlabel('feature 1')
        pyplot.ylabel('feature 2')
        
        # plot mutual information
        pyplot.figure()
        pyplot.plot([s.mutual_information for s in model.stats])
        pyplot.xlabel('learning steps')
        pyplot.ylabel('mutual information')
        
    pyplot.show()
    
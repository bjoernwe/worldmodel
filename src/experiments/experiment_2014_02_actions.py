import numpy as np
from matplotlib import pyplot

import worldmodel

from envs import env_circle
from envs import env_cube
from envs import env_noise


if __name__ == '__main__':
    
    #env = env_circle.EnvCircle(seed=None)
    env = env_cube.EnvCube(step_size=0.2, sigma=0.05, ndim=2, seed=None)
    #env = env_noise.EnvNoise(sigma=0.1, ndim=2, seed=None)
    data, actions, _ = env.do_random_steps(num_steps=10000)
    
    #print data
    #print map(lambda a: env.get_actions_dict()[a], actions)

    model = worldmodel.Worldmodel(method='fast', uncertainty_prior=100, factorization_weight=0, seed=None)
    model.add_data(data=data, actions=actions)
    
    for i in range(4):
        model.split(action=None, min_gain=float('-inf'))
    
    for i in range(env.get_number_of_possible_actions()):
        print env.get_actions_dict()[i], ':', model.partitionings[i].tree._split_params._test_params    
        pyplot.subplot(2, 2, i+1)
        pyplot.title(env.get_actions_dict()[i])
        model.plot_data_colored_for_state(active_action=i, show_plot=False)
        model.plot_state_borders(active_action=i, show_plot=False, resolution=100)
        #model.partitionings[i].plot_transitions()
        #data = model.data[np.where(model.actions == i)]
        #pyplot.plot(data[:,0], data[:,1], '.')
        #for leaf in model.get_partitioning(action=i).tree.get_leaves():
        #    leaf.plot_gradient()
    
    pyplot.show()
    
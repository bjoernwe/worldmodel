"""
Visualizes the largest/smallest eigenvectors of a graph.
"""

import numpy as np
import scipy.linalg
import scipy.spatial

from matplotlib import pyplot

from studienprojekt.env_cube import EnvCube


def get_graph(data, fast_partition, k=5, normalize=False):
    
    # pairwise distances
    distances = scipy.spatial.distance.pdist(data)
    distances = scipy.spatial.distance.squareform(distances)

    # transition matrix
    N, _ = data.shape
    W = np.zeros((N, N))
    #W += -1e-8

    # transitions to neighbors
    # s - current node
    # t - neighbor node
    for s in range(N-1):
        indices = np.argsort(distances[s])  # closest one should be the point itself
        for t in indices[0:k+1]:
            if s != t:
                W[s,t] = 1
                W[t,s] = 1

    # transitions to successors
    # s - current node
    # t - neighbor node
    # u - following node
    for s in range(N-1):
        indices = np.argsort(distances[s])  # closest one should be the point itself
        for t in indices[0:k+1]:
            u = t+1
            if u >= N:
                continue
            if fast_partition:
                W[s,u] = -1
                W[u,s] = -1
            else:
                W[s,u] = 1
                W[u,s] = 1
                
    # normalize matrix
    if normalize:
        d = np.sum(W, axis=1)
        for i in range(N):
            if d[i] > 0:
                W[i] = W[i] / d[i]
            
    return W


if __name__ == '__main__':

    # parameters
    steps = 2000
    fast = True
    k = 15
    normalize = True
    smallest = False
    laplacian = False
    plot_sign = False
    
    # data
    env = EnvCube(step_size=0.2, sigma=0.01)
    #env = EnvCube(step_size=0.1, sigma=0.05)
    print env.get_available_actions()
    data, actions = env.do_random_steps(num_steps=steps)
    
    # get eigenvalues
    W = get_graph(data=data, fast_partition=fast, k=k, normalize=normalize)
    if laplacian:
        W = np.diag(np.sum(W, axis=1)) - W
    E, U = scipy.linalg.eig(a=W)
    
    # sort eigenvalues
    E = np.real(E)
    idx = np.argsort(np.real(E))
    #idx = np.argsort(np.abs(E))
    
    # plot
    print 'steps=%d, k=%d, fast=%s,\n normalize=%s, smallest=%s' % (steps, k, fast, normalize, smallest)
    pyplot.figure()
    cm = pyplot.cm.get_cmap('summer')
    for i in range(15):
        if smallest:
            j = idx[i]    # smallest
        else:
            j = idx[-i-1]   # largest
        pyplot.subplot(3, 5, i+1)
        if plot_sign:
            pyplot.scatter(x=data[:,0], y=data[:,1], c=np.sign(np.real(U[:,j])), edgecolors='none', cmap=cm)
        else:
            pyplot.scatter(x=data[:,0], y=data[:,1], c=(np.real(U[:,j])), edgecolors='none')#, vmin=-7, vmax=7)
        pyplot.title(str(E[j]))
        pyplot.colorbar()
        
    pyplot.show()
    
import numpy as np
import unittest

import worldmodel
from numpy.ma.testutils import assert_almost_equal


class DataReferencesTest(unittest.TestCase):
    
    def testTransitionRefs(self):
        """
        Generate some simple transitions and verify correctness of getter
        functions. 
        """
        # generate some test data
        data = np.zeros((4, 2))
        data[0] = [ 3.0, -1]
        data[1] = [ 1.0, -1]
        data[2] = [-1.0,  1]
        data[3] = [-3.0,  1]
        actions = [None, 0, 1, 0]
        # add data to model
        model = worldmodel.WorldModel(method='pca')
        model.add_data(data=data, actions=actions)
        # transitions in one single state
        self.assertEqual(model.tree._get_transition_refs(heading_in=False, inside=False, heading_out=False), [[], []])
        self.assertEqual(model.tree._get_transition_refs(heading_in=True, inside=False, heading_out=False), [[], []])
        self.assertEqual(model.tree._get_transition_refs(heading_in=False, inside=True, heading_out=False), [[0, 1, 2], [1, 2, 3]])
        self.assertEqual(model.tree._get_transition_refs(heading_in=False, inside=False, heading_out=True), [[], []])
        # more data and split node
        for _ in range(99):
            model.add_data(data, actions=actions)
        model.single_splitting_step()
        # test again with two states
        leaf1, _ = model.tree.get_leaves()
        refs1, refs2 = leaf1._get_transition_refs(heading_in=True, inside=False, heading_out=False)
        self.assertEqual([refs1[:2], refs2[:2]], [[3, 7], [4, 8]])
        refs1, refs2 = leaf1._get_transition_refs(heading_in=False, inside=True, heading_out=False)
        self.assertEqual([refs1[:2], refs2[:2]], [[0, 4], [1, 5]])
        refs1, refs2 = leaf1._get_transition_refs(heading_in=False, inside=False, heading_out=True)
        self.assertEqual([refs1[:2], refs2[:2]], [[1, 5], [2, 6]])
        # test again with action
        refs1, refs2 = leaf1._get_transition_refs_for_action(action=None, heading_in=True, inside=False, heading_out=False)
        self.assertEqual([refs1[:2], refs2[:2]], [[3, 7], [4, 8]])
        refs1, refs2 = leaf1._get_transition_refs_for_action(action=0, heading_in=False, inside=True, heading_out=False)
        self.assertEqual([refs1[:2], refs2[:2]], [[0, 4], [1, 5]])
        refs1, refs2 = leaf1._get_transition_refs_for_action(action=1, heading_in=False, inside=False, heading_out=True)
        self.assertEqual([refs1[:2], refs2[:2]], [[1, 5], [2, 6]])
        return True
        


class DataTests(unittest.TestCase):

    def testNChain1(self):
        n = 100
        data = worldmodel.problemChain(n)
        self.assertEqual(data.shape[0], n)
        
    def testNChain2(self):
        n = 10000
        data = worldmodel.problemChain(n)
        self.assertEqual(data.shape[0], n)

    def testChainRandom(self):
        data = worldmodel.problemChain(n=1)
        x1 = list(data[0])
        data = worldmodel.problemChain(n=1)
        x2 = list(data[0])
        self.assertNotEqual(x1, x2)

    def testChainSeed(self):
        data = worldmodel.problemChain(n=1, seed=0)
        x1 = list(data[0])
        data = worldmodel.problemChain(n=1, seed=0)
        x2 = list(data[0])
        self.assertEqual(x1, x2)


class TrivialTransitionsTest(unittest.TestCase):

    def testTrivialTransMatrix(self):
        data = worldmodel.problemChain(n=1000, seed=0)
        model = worldmodel.WorldModel()
        model.add_data(data)
        trans = model._merge_transition_matrices()
        self.assertEqual(trans.shape, (1,1))
        self.assertEqual(trans[0,0], data.shape[0]-1) # n of transitions

        

class TrivialEntropyTests(unittest.TestCase):

    def setUp(self):
        self.data = worldmodel.problemChain(n=1000, seed=0)

    def testTrivialEntropy(self):
        model = worldmodel.WorldModel()
        model.add_data(self.data)
        transitions = model._merge_transition_matrices()
        entropy = model._matrix_entropy(transitions=transitions, normalize=False)
        self.assertEqual(entropy, 1.0)

    def testTrivialTransEntropy(self):
        tree = worldmodel.WorldModel()
        tree.add_data(self.data)
        transitions = tree._merge_transition_matrices()
        entropy = worldmodel.WorldModel._matrix_entropy(transitions=transitions)
        self.assertEqual(entropy, 1.0)



class VectorEntropyTests(unittest.TestCase):

    def testZeroEntropy(self):
        for i in range(10):
            zeros = np.zeros(i)
            entropy = worldmodel.WorldModel._entropy(dist=zeros, normalize=True, ignore_empty_classes=True)
            self.assertEqual(entropy, 1.0)
        for i in range(2,10):
            zeros = np.zeros(i)
            entropy = worldmodel.WorldModel._entropy(dist=zeros, normalize=False, ignore_empty_classes=True)
            self.assertEqual(entropy, np.log2(i))

    def testOneEntropy(self):
        for i in range(2,10):
            ones = np.ones(i)
            entropy = worldmodel.WorldModel._entropy(dist=ones, normalize=True)
            self.assertEqual(entropy, 1.0)
        for i in range(2,10):
            ones = np.ones(i)
            entropy = worldmodel.WorldModel._entropy(dist=ones, normalize=False)
            self.assertEqual(entropy, np.log2(i))

    def testCustomEntropy(self):

        # normalized
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(2)), normalize=True)
        self.assertEqual(entropy, 0.0)
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(3)), normalize=True)
        self.assertEqual(entropy, 0.5793801642856950)
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(4)), normalize=True)
        self.assertEqual(entropy, 0.72957395851362239)

        # not normalized
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(2)), normalize=False)
        self.assertEqual(entropy, 0.0)
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(3)), normalize=False)
        self.assertEqual(entropy, 0.91829583405448956)
        entropy = worldmodel.WorldModel._entropy(dist=np.array(range(4)), normalize=False)
        self.assertEqual(entropy, 1.4591479170272448)

    def testRandomEntropy(self):
        """
        Checks wether entropy of random vectors stays between 0 and 1.
        """
        np.random.seed(0)
        for l in range(10):
            for _ in range(1000):
                p = l * np.random.random(l)
                e = worldmodel.WorldModel._entropy(dist=p, normalize=True)
                self.assertGreaterEqual(e, 0.)
                self.assertLessEqual(e, 1.)

        for l in range(2, 10):
            for _ in range(1000):
                p = l * np.random.random(l)
                e = worldmodel.WorldModel._entropy(dist=p, normalize=True)
                self.assertGreaterEqual(e, 0.)
                self.assertLessEqual(e, np.log2(l))
                
    def testMutualInformation(self):
        """
        """
        # 'useless' Markov Chain
        S = 10 * np.ones((8, 8))
        assert_almost_equal(0.0, worldmodel.WorldModel._mutual_information(transition_matrix=S))
        
        # deterministic Markov Chain
        T = np.zeros((8, 8))
        for i in range(8):
            T[i,(i+1)%8] = 80
        assert_almost_equal(3.0, worldmodel.WorldModel._mutual_information(transition_matrix=T))
        
        # test mixture
        assert_almost_equal(1.5, worldmodel.WorldModel._mutual_information_average(transition_matrices=[S, T]))


if __name__ == "__main__":
    unittest.main()

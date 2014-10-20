from datetime import timedelta
import unittest

from preservationist import generateBinBoundaries

T1 = timedelta(hours=1)
T2 = timedelta(hours=3)
T3 = timedelta(hours=4)
T4 = timedelta(hours=5)
T5 = timedelta(hours=6)

class TestGenerateBinBoundaries(unittest.TestCase):

    def testEmpty(self):
        self.assertEqual([],list(generateBinBoundaries([])))

    def testSingletonEmpty(self):
        self.assertEqual([],list(generateBinBoundaries([iter([])])))

    def testSingletonSingleton(self):
        self.assertEqual([T1],list(generateBinBoundaries([iter([T1])])))

    def testSingletonList(self):
        self.assertEqual([T1,T2,T3],list(generateBinBoundaries([iter([T1,T2,T3])])))

    def testTwoEqualSingletons(self):
        self.assertEqual([T1],list(generateBinBoundaries([iter([T1]),iter([T1])])))

    def testTwoInequalSingletons(self):
        self.assertEqual([T1,T2],list(generateBinBoundaries([iter([T1]),iter([T2])])))

    def testMultipleLists(self):
        self.assertEqual([T1,T2,T3,T4,T5],list(generateBinBoundaries([iter([T1,T3]),iter([T2,T4]),iter([T1,T3,T5]),iter([T4,T5])])))


if __name__ == '__main__':
    unittest.main()
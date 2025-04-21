"""Abstract base graph-form class module

This module contains the abstract base class for graph-form component classes

separable function key:

0:          g(x) = 0
abs:        g(x) = |x|
huber:      g(x) = huber(x)
card:       g(x) = { 0 if x = 0
                   { 1 otherwise
nonneg:     g(x) = I(x >= 0)
nonpos:     g(x) = I(x <= 0)
box:        g(x) = I(0 <= x <= 1)
finite_set: g(x) = I(x ∈ S)

Author: Bennet Meyers
"""

from abc import ABC, abstractmethod
import numpy as np
import scipy.sparse as sp
import itertools as itt


class GraphComponent(ABC):
    def __init__(self, weight, T, p, diff=0, **kwargs):
        self._weight = weight
        self._T = T
        self._p = p
        self._x_size = T * p
        self._diff = diff
        self.__set_z_size()
        self.__make_P()
        self._Px = sp.dok_matrix(2 * (self.x_size))
        self._P = sp.block_diag([self._Px, self._Pz])
        self.__make_gz()
        self._gx = [{"f": 0, "args": None, "range": (0, self.x_size - 1)}]
        self._g = itt.chain.from_iterable([self._gx, self._gz])
        self.__make_A()
        self.__make_B()
        self.__make_c()
        return

    def make_dict(self):
        canonicalized = {
            "P": self._P,
            "q": self._q,  # not currently used
            "r": self._r,  # not currently used
            "A": self._A,
            "B": self._B,
            "c": self._c,
            "g": self._g,
        }
        return canonicalized

    def __set_z_size(self):
        self._z_size = (self._T - self._diff) * self._p

    def __make_P(self):
        self._Pz = sp.dok_matrix(2 * (self.z_size))

    def __make_q(self):
        self._q = None

    def __make_r(self):
        self._r = None

    def __make_gz(self):
        self._gz = [
            {"g": 0, "args": None, "range": (self.x_size, self.x_size + self.z_size)}
        ]

    def __make_A(self):
        if self._diff == 0:
            self._A = sp.eye(self.x_size)
        elif self._diff == 1:
            T = self._T
            m1 = sp.eye(m=T - 1, n=T, k=0)
            m2 = sp.eye(m=T - 1, n=T, k=1)
            self._A = m2 - m1
        elif self._diff == 2:
            T = self._T
            m1 = sp.eye(m=T - 2, n=T, k=0)
            m2 = sp.eye(m=T - 2, n=T, k=1)
            m3 = sp.eye(m=T - 2, n=T, k=2)
            self._A = m1 - 2 * m2 + m3
        elif self._diff == 3:
            T = self._T
            m1 = sp.eye(m=T - 3, n=T, k=0)
            m2 = sp.eye(m=T - 3, n=T, k=1)
            m3 = sp.eye(m=T - 3, n=T, k=2)
            m4 = sp.eye(m=T - 3, n=T, k=3)
            self._A = -m1 + 3 * m2 - 3 * m3 + m4
        else:
            print("Differences higher than 3 not supported")
            raise Exception

    def __make_B(self):
        self._B = sp.eye(self.z_size) * -1

    def __make_c(self):
        self._c = np.zeros(self.z_size)

    def __add_constraints(self):
        if self._vmin is not None:
            # introduces new internal variable z
            self._z_size += self.x_size
            self._P = sp.block_diag([self._P, sp.dok_matrix(2 * (self.x_size,))])
            self._g = np.concatenate([self._g, 2 * np.ones(self.x_size)])
            self._A = sp.bmat([[self._A], [sp.eye(self.x_size)]])
            self._B = sp.block_diag([self._B, -sp.eye(self.x_size)])
            self._c = np.concatenate([self._c, self._vmin * np.ones(self.x_size)])
        if self._vmax is not None:
            # introduces new internal variable z
            self._z_size += self.x_size
            self._P = sp.block_diag([self._P, sp.dok_matrix(2 * (self.x_size,))])
            self._g = np.concatenate([self._g, 2 * np.ones(self.x_size)])
            self._A = sp.bmat([[self._A], [sp.eye(self.x_size)]])
            self._B = sp.block_diag([self._B, sp.eye(self.x_size)])
            self._c = np.concatenate([self._c, self._vmax * np.ones(self.x_size)])
        if self._vavg is not None:
            # introduces new constraints on x, but no new helper var
            newline = sp.coo_matrix(
                (np.ones(self.x_size), (self.x_size * [1], np.arange(self.x_size)))
            )
            self._A = sp.bmat([[self._A], [newline]])
            self._b = sp.bmat([[self._A], [sp.dok_matrix((1, self.z_size))]])
            self._c = np.concatenate([self._c, [self._vavg]])

        if self._period is not None:
            # TODO: implement this
            pass
        if self._first_val is not None:
            # TODO: implement this
            pass

    @property
    def weight(self):
        return self._weight

    def set_weight(self, weight):
        self._weight = weight
        return

    @property
    def T(self):
        return self._T

    @property
    def p(self):
        return self._p

    @property
    def size(self):
        return self.x_size + self.z_size

    @property
    def x_size(self):
        return self._x_size

    @property
    def z_size(self):
        return self._z_size

    @property
    def P_x(self):
        return self._P

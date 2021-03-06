import numpy as np
from util import *

class GFn:
    def __init__( self, value, nbit, dump=False ):
        self.nbit = nbit
        # print('value = ', value)
        if np.isscalar(value):
            if value == 0:
                value_array = np.array([0]*nbit)
            else:
                bin_list = [int(i) for i in bin(value)[2:]]
                value_array = np.flip( [0]*(nbit-len(bin_list)) + bin_list, axis=0 )

        elif len(np.shape(value)) is 1:
            if np.shape(value)[0] > nbit:
                value_array = fit_gfn( value, nbit )
            elif np.shape(value)[0] < nbit:
                value_array = np.append( value, np.zeros(nbit-np.shape(value)[0]) )
            else:
                value_array = np.array(value)

        if value_array.shape[0] is not nbit:
            print("shape = ", value_array.shape)
            print("ideal = ", (nbit,))
            raise Exception
        self.value = np.array(value_array).astype(int)
        self.dump = dump

    def __radd__( self, a ):
        if self.dump:
            print("radd(", str(self), ",", a, type(a), ")")
        if int(a) == 0: return GFn( self.value, self.nbit)
        print("radd: Add with non-zero")
        raise Exception()

    def __add__( self, a ):
        if self.dump:
            print("add(", str(self), self.value.shape, ",", a, type(a), ")")
        if type(a) is not type(GFn(np.array([0]),1)):
            if int(a) == 0: return GFn(self.value, self.nbit)        
        if self.value.shape[0] is not a.value.shape[0]:
            err_msg = "Mismatched size in GFn addition"
            err_msg += ", augend is ", self.value.shape
            err_msg += ", addend is ", a.value.shape
            raise ValueError()
        result_value = fit_gfn( a.value + self.value, self.nbit)
        result = GFn( result_value, self.nbit)
        if self.dump:
            print("add return ", str(result))
        return result

    def __sub__( self, a ):
        return self+a

    def __rmul__( self, a ):
        if self.dump:
            print("rmul(", str(self), ",", a, type(a), ")")
        result_value = np.remainder( a*self.value, 2 )
        result = GFn( result_value, self.nbit )
        if self.dump:
            print("rmul return ", str(result), type(result))
        return result 

    def __mul__( self, a ):
        if self.dump:
            print("mul(", str(self), self.value.shape, ",", a, type(a), ")")
        if len(self.value.shape) > 1:
            raise ValueError

        # If multiplicend is an array, separte it into elements
        if type(a) is type(np.array([])):
            return a.__rmul__(self)

        if np.isscalar(a):
            value = a*self.value
            return GFn( fit_gfn(value, self.nbit), self.nbit)

        if type(a) is not type(GFn(0,1)):
            print("type is", type(a))
            raise ValueError( str(a) + "is neither GFn or np.array")

        # Shift multiplicend and add it to psum
        product = np.zeros_like(self.value, dtype=int).astype(int)
        for i in range( 0, self.nbit ):

            # Partial sum = [0]*i + self*a
            psum = np.append( np.zeros(i), self.value[i]*a.value)
            psum = fit_gfn( psum, self.nbit )
            if psum.size != self.nbit:
                print("Size mismatch1")
                raise Exception
            product = product + psum
            product = fit_gfn( product, self.nbit )
            if product.size != self.nbit:
                print("Size mismatch2")
                raise Exception
        product = fit_gfn( product, self.nbit )

        if product.shape[0] is not a.nbit:
            print("mul(", str(self), self.value.shape, ",", a, type(a), ")")
            print("self.nbit = ", self.nbit)
            print("a.nbit = ", a.nbit)
            print("Size mismatch3")
            raise Exception()

        result = GFn( product, a.nbit )
        if self.dump:
            print("Return GFn(", str(result), ")")

        return GFn( product, a.nbit )

    def __eq__( self, a ):
        if type(a) is not type(GFn(0,1)):
            return int(self) == a
        if not self.nbit == a.nbit:
            raise ValueError("GFn compare two input with different bit length")
            return False
        return np.array_equal(self.value, a.value)

    def __repr__( self ):
        return 'GFn(' + str(self) + ')'

    def __float__(self):
        return float(int(self))

    def __int__(self):
        total = 0
        for i, digit in enumerate(reversed(self.value)):
            total = total*2 + int(digit)
        return total

    def __str__(self):
        out_str = ""
        for x in self.value:
            out_str = str(x) + out_str
        return out_str

    def iszero(self):
        if np.count_nonzero(self.value) > 0: return False
        return True

    def toGF2(self,n):
        if n < self.nbit:
            return GFn( self.value[:n], n )
        else:
            return GFn( np.append(self.value, np.zeros(n-self.nbit)), n )

    def power(self,n):
        e = GFn(1,self.nbit)
        for i in range(0,n):
            e = e*self
        return e

    def log_a(self):
        alpha = GFn(2,self.nbit)
        for i in range(0,2**self.nbit):
            if alpha.power(i) == self:
                return i

    def __exp__(self,n):
        return self.power(n)

    def is_root(self, g):
        y = np.polyval(g,self)
        return y.iszero()

    def inverse(self):
        for i in range(0,2**self.nbit):
            if int( GFn(i,self.nbit) * self )==1:
                return GFn(i,self.nbit)

class GFn_poly:
    def __init__( self, value, nbit=None ):
        if type(value) is int:
            self.value = np.poly1d([GFn(value,nbit)])
            self.nbit = nbit
        elif type(value) is type(GFn(0,1)):
            self.value = np.poly1d([value])
            self.nbit = value.nbit
        elif type(value) is type(np.array([])):
            self.value = np.poly1d(value)
            self.nbit = value[0].nbit
        elif type(value) is list and type(value[0]) is int:
            self.value = np.poly1d(intlist_to_gfpolylist( value, nbit ))
            self.nbit = nbit
        elif type(value) is list and type(value[0]) is type(GFn(0,1)):
            self.value = np.poly1d(value)
            self.nbit = value[0].nbit
        elif type(value) is type(np.poly1d([])) and type(value[0]) is type(GFn(0,1)):
            self.value = value
            self.nbit = value[0].nbit
        elif type(value) is type(np.poly1d([])):
            value_int = [int(s) for s in value]
            value_gfn = intlist_to_gfpolylist( value_int, nbit )
            self.value = np.poly1d(value_gfn)
            self.nbit = nbit
        elif type(value) is str:
            value_int  = [int(s) for s in value]
            self.value = np.poly1d(intlist_to_gfpolylist( value_int, nbit ))
            self.nbit = nbit
        else:
            print("type is ", type(value))
            raise ValueError

        self.c = self.value.c
        self.order = self.value.order
        if type(self.value[0]) is not type(GFn(0,1)) and not self.value[0] == 0.0:
            print("self.value[0] is not 0.0 = ", self.value[0] == 0.0)
            print("value[0] = ", self.value[0])
            raise ValueError

    def __repr__( self ):
        return str(self.value)

    def __iter__( self ):
        return iter(self.value)

    def __add__( self, b ):
        if type(b) is type(GFn_poly(0,1)):
            return GFn_poly( np.polyadd(self.value,b.value), self.nbit )
        else:
            print("type is ", type(b))
            raise ValueError

    def __mul__( self, b ):
        if type(b) is type(np.poly1d([])):
            return GFn_poly( np.polymul(self.value,b), self.nbit )
        elif type(b) is type(GFn_poly(0,1)):
            return GFn_poly( np.polymul(self.value,b.value), self.nbit )
        elif type(b) is float:
            if b == 0.0: return GFn_poly(0, self.nbit)
            else: raise ValueError
        elif type(b) is type(GFn(0,1)):
            return GFn_poly(self.value*b)
        else:
            print("Target type is ", type(b), b)
            raise ValueError

    def __truediv__( self, b ):
        leader_coeff = self.value.c[0] * b.value.c[0].inverse()
        leader_order = self.value.order - b.value.order
        qx = (GFn_poly([leader_coeff]) << leader_order)
        rx = self + qx*b
        while rx.order >= b.value.order:
            qx, rx = qx+rx/b, rx%b
        return qx

    def __mod__( self, mod ):
        leader_coeff = self.value.c[0] * mod.value.c[0].inverse()
        leader_order = self.value.order - mod.value.order
        qx = (GFn_poly([leader_coeff]) << leader_order)
        rx = self + qx*mod
        while rx.order >= mod.value.order:
            qx, rx = qx+rx/mod, rx%mod
        return rx

    def __lshift__(self, shift):
        zero = GFn(0,self.nbit)
        one  = GFn(1,self.nbit)
        poly = np.polymul(self.value,np.poly1d([one]+[zero]*shift))
        return GFn_poly(poly)

    def __call__(self, a):
        return np.polyval( self.value, a )

    def __getitem__( self, a ):
        return self.value[a]

    def __eq__( self, b ):
        if self.value.order is not b.value.order:
            return False
        else:
            for c0, c1 in zip( self.value.c, b.value.c ):
                if not c0 == c1:
                    return False
            return True

    def derivative(self):
        return GFn_poly(np.polyder(self.value))

    def map_to( self, trg ):
        table = gf_map( self.value[0].nbit, trg )
        gen_gfm_coeffs = []
        for b in self.value:
            gen_gfm_coeff = [s[1] for s in table if s[0]==b][0]
            gen_gfm_coeffs.append( gen_gfm_coeff )
        return GFn_poly(gen_gfm_coeffs)


def intlist_to_gfpolylist( int_list, m ):
    return [GFn(g,m) for g in int_list]

def symbol_all( nbit ):
    ret_list = []
    for i in range(0,2**nbit):
        ret_list.append(GFn(i,nbit))
    return ret_list

def find_characteristic( a ):
    i = 1
    product = a
    while 1:
        if int(product) == 1: return i+1
        product = product*a
        i = i+1

def gfn_array_modulo( dividend, modular_poly ):
    logq = dividend[0].nbit
    zero_logq = GFn(0,logq)
    one_logq  = GFn(1,logq)

    modular = np.array(modular_poly)
    while 1:

        # Remainder is 0, return with padding or slicing
        if np.argwhere(dividend!=zero_logq).size == 0:
            if len(dividend) < len(modular):
                return np.append( [zero_logq] * (len(modular)-len(dividend)-1), dividend )
            else:
                return dividend[-len(modular):]

        msb = np.min(np.argwhere(dividend!=zero_logq),axis=0)[0]

        # Degree of modular is less than dividend
        if msb > len(dividend) - len(modular):
            if len(dividend) < len(modular):
                return np.append( [zero_logq] * (len(modular)-len(dividend)-1), dividend )
            else:
                return dividend[-len(modular):]

        # Do padding to align the MSB of modular to the dividend
        remainder = np.append( [zero_logq] * msb, modular )
        remainder = np.append( remainder, [zero_logq] * (len(dividend) - msb - len(modular)))
        remainder = remainder * dividend[msb]

        # Obtain the result from polynomial addition
        result = np.empty(len(dividend), dtype=object)
        for i, x in enumerate(result):
            result[i] = dividend[i]+remainder[i]
        dividend = result

def gen_zero_one_alpha_overGFq( q ):
    import math
    logq = int(math.log2(q))
    if q<4:
        return GFn(0,logq), GFn(1,logq), None
    else:
        return GFn(0,logq), GFn(1,logq), GFn(2,logq)

def gf_map( a, b, verbose=0 ):

    if a>b:
        s = int((2**a-1)/(2**b-1))
        if b==1:
            src = [GFn(1,a)]
            trg = [GFn(1,1)]
        else:
            alpha = GFn(2,a)
            src = [alpha.power(i) for i in range(0,2**a-1,s)]
            trg = [GFn(2,b).power(i) for i in range(0,2**b-1) ]
    elif a<b:
        s = int((2**b-1)/(2**a-1))
        if a==1:
            src = [GFn(1,1)]
            trg = [GFn(1,b)]
        else:
            alpha = GFn(2,a)
            src = [alpha.power(i) for i in range(0,2**a-1)]
            trg = [GFn(2,b).power(i) for i in range(0,2**b-1,s) ]
    else: raise ValueError

    if verbose:
        print("alpha^"+str(s), "in GF( 2^"+str(a),") = beta in GF( 2^"+str(b), ")")
    table = [(GFn(0,a), GFn(0,b) )]
    for i,xy in enumerate(zip(src,trg)):
        x,y = xy
        if verbose:
            print("#", i, "(alpha^"+str(s)+")^"+str(i), " = ", x, "on GF( 2^"+str(a),") = beta^"+str(i), "in GF( 2^"+str(b), ")")
        table.append((x,y))
    if verbose:
        print("--")
    return table

def weight( f ):
    int_list = [int(x) for x in f]
    non_zero_list = [x>0 for x in int_list]
    return sum(non_zero_list)

def finding_roots( g, ext, alpha, method ):
    index = []
    roots  = []

    if method == 'chien':
        terms = []
        for i, coef in enumerate(reversed(g.c)):
            terms.append(coef)

        for p in range(1, 2**ext-1):
            for i, coef in enumerate(reversed(g.c)):
                terms[i] *= alpha.power(i)
            value = sum(terms)
            if value.iszero():
                index.append(p)
                roots.append(alpha.power(p))
    elif method == 'brute-force':
        alpha_powers = [alpha.power(i) for i in range(2**ext-1)]
        for i, x in enumerate(alpha_powers):
            if g(x).iszero():
                index.append(i)
                roots.append(x)
    else:
        print("method = ", method)
        raise ValueError()

    return index, roots

def find_roots( x_list, g, ext ):
    index = []
    roots  = []
    base = g[0].nbit
    if base is not ext:
        g_ext = poly_map( g, base, ext )
    else:
        g_ext = g

    for i, x in enumerate(x_list):
        if int(g_ext(x)) == 0:
            index.append(i)
            roots.append(x)
    return index, roots

def determinant( M ):
    import itertools
    fld = M.flatten()[0].nbit
    det = GFn(0,fld)
    for indexs in itertools.permutations(list(range(M.shape[0]))):
        product = GFn(1,fld)
        for row, col in enumerate(indexs):
            product *= M[row][col]
        det += product
    return det
import numpy as np
import GFn
from util import gf2_remainder, fit_gfn, sep, step_msg_manager
from fractions import gcd
import math
import argparse
import bound

def Berlekamp_Massey( syndrones, verbose=0 ):
	zero_ext, one_ext, alpha_ext = GFn.gen_zero_one_alpha_overGFq(2**syndrones[0].nbit)
	s = GFn.GFn_poly(syndrones)
	c = GFn.GFn_poly(1,syndrones[0].nbit) # ([one_ext])
	B = GFn.GFn_poly(1,syndrones[0].nbit) # ([one_ext])
	L = 0
	m = 1
	n = 0
	b = one_ext
	for n in range(0,len(syndrones)):

		psum = zero_ext
		for i in range(1,L+1):
			psum += c[i] * s[n-i]
		d = s[n] + psum

		if int(d) == 0:
			m += 1
		elif 2*L <= n:
			t = c
			dbinv = d*b.inverse()
			c += (GFn.GFn_poly(dbinv) << m) * B
			L = n+1-L
			B = t
			b = d
			m = 1
		else:
			c += (GFn.GFn_poly(dbinv) << m) * B
	if verbose:
		print("Berlekamp-Massey Algorithm")
		print("Locator polynomial = \n", c)
	return c

def Euclidean( sx, v, verbose=0 ):
	tx = GFn.GFn_poly(1,log_ext) << (2*v)

	A00, A01 = GFn.GFn_poly(1,log_ext), GFn.GFn_poly(0,log_ext)
	A10, A11 = GFn.GFn_poly(0,log_ext), GFn.GFn_poly(1,log_ext)

	while sx.order >= v:
		qx, rx = tx / sx, tx % sx
		sx, tx = rx, sx
		A00, A01, A10, A11 = qx*A00+A10, qx*A01+A11, A00, A01

	lamda = A00(0).inverse()
	sigma = A00 * lamda
	eva_poly = sx * lamda
	if verbose:
		print("Euclidean Algorithm")
		print("Locator polynomial = \n", sigma)
		print("Evaluation polynomial = \n", eva_poly)
	return sigma, eva_poly

def get_Mw( r, w ):
	e_arr = []
	for i in range( 0, w ):
		row = []
		for j in range( 0, w ):
			row.append(r(alpha_ext.power(i+j)))
		e_arr.append(row)
	return np.array(e_arr)

def check_generalized_newtons_identities( poly, loc_pair ):
	j = 2
	print("poly = ", poly)

	total = zero_ext
	print("total = ", total)
	for i, sigma_i in enumerate(reversed(poly.c)):
		total += sigma_i * get_E( loc_pair, len(poly)+1-i )
		print("total = sigma[", i, "](", sigma_i, ") * E[", len(poly)+1-i, "](", get_E( loc_pair, len(poly)+1-i ), ")")
	print("total = ", total, total.iszero())
	if not total.iszero():
		raise ValueError
	return

def check_eva_poly( loc_pair, b0=1 ):
	eva_poly = GFn.GFn_poly(0,log_ext)
	for loc in loc_pair:
		product = GFn.GFn_poly(1,log_ext)
		for X in [_loc[0] for _loc in loc_pair]:
			if X is not loc[0]:
				product *= GFn.GFn_poly([X, one_ext])
		sca = loc[1] * loc[0].power(b0)
		eva_poly += product * sca
	return eva_poly


if __name__ == "__main__":

	step = step_msg_manager()

	parser = argparse.ArgumentParser(description="Flip a switch by setting a flag")
	parser.add_argument('--verbose', action='store_true')
	parser.add_argument('--ex')
	parser.add_argument('--cx')
	parser.add_argument('--rx')
	parser.add_argument('--epoly',    default='berlekamp')
	parser.add_argument('--findroot', default='chien')
	parser.add_argument('--d0', type=int)
	parser.add_argument('--n',  type=int, default=15)
	parser.add_argument('--q',  type=int, default=4)
	parser.add_argument('--v',  type=int)
	args = parser.parse_args()

	n = args.n
	q = args.q
	m = bound.find_m(n,q)
	b0 = 1
	log_q = int(math.log2(q))
	log_ext = m * log_q

	zero_q,   one_q,   alpha_q   = GFn.gen_zero_one_alpha_overGFq(q)
	zero_ext, one_ext, alpha_ext = GFn.gen_zero_one_alpha_overGFq(2**log_ext)

	# Setting received polynomial r(x)
	step.show("Define received polynomial r(x)", verbose=args.verbose)
	if args.rx is not None:
		r_poly = GFn.GFn_poly( args.rx, log_q )
		r_ext  = r_poly.map_to(log_ext)
		if args.d0 is None:
			print("Given received polynomial should provide designed d0")
			raise ValueError("Given received polynomial should provide designed d0")
		d0 = args.d0
		if args.verbose:
			print("Given received polynomial = \n", r_poly)
			print("Given designed minimum distance d0 = ", d0)

	# No r(x) defined, setting codeword polynomial c(x) and error poly e(x)
	elif args.cx is not None:
		# Setting codeword polynomial c(x)
		c_poly = GFn.GFn_poly( args.cx, log_q )
		c_ext = c_poly.map_to(log_ext)
		d0 = bound.find_tzeng(  g=c_ext, n=n, ext=log_ext )
		if args.verbose:
			print("codeword polynomial = ", c_poly.c, "\n", c_poly)
			print("codeword minimum distance (with Tzeng's) d0 = ", d0)

		# Setting error polynomial e(x)
		if args.ex is not None:
			e_poly = GFn.GFn_poly( args.ex, log_q )
			e_ext = e_poly.map_to(log_ext)
			if args.verbose:
				print("error polynomial = ", e_poly.c, "\n", e_poly)
			r_ext = c_ext + e_ext

		else:
			e_int = [1,1,0,0]
			e_poly = GFn.GFn_poly(e_int,log_q)
			e_ext = e_poly.map_to(log_ext)
			if args.verbose:
				print("error polynomial = ", e_poly.c, "\n", e_poly)
			r_ext = c_ext + e_ext

			# Obtain given location pair from given e(x)
			given_loc_pair = []
			for e, c in enumerate(e_ext):
				if not c.iszero():
					given_loc_pair.append((alpha_ext.power(e_ext.order-e), c))
			if args.verbose:
				print("given locator pair (X,Y) = ", given_loc_pair)

			# Obtain given locator polynomial
			given_loc_poly = GFn.GFn_poly(1,log_ext)
			for loc in given_loc_pair:
				given_loc_poly *= GFn.GFn_poly([loc[0], one_ext])
			if args.verbose:
				print("given locator polynomial = ", given_loc_poly.c, "\n", given_loc_poly)
		
			given_eva = check_eva_poly( given_loc_pair, b0 )

	# Neither r(x) nor c(x) is defined, setting default r(x)
	else:
		r_int  = [1,1,1,1,1,0,0,1,1]
		r_poly = GFn.GFn_poly(r_int,log_q)
		r_ext  = r_poly.map_to(log_ext)
		d0 = 5
		if args.verbose:
			print("Given received polynomial = \n", r_ext)
			print("Given designed minimum distance d0 = ", d0)

	# Find error number v
	step.show("Find error number v", verbose=args.verbose)
	if args.v is not None: v = args.v
	else:
		if args.verbose:
			print("No given error number v")
		v = None
		for test_w in range( int(d0/2), -1, -1 ):
			Mw = get_Mw( r_ext, test_w )
			det = GFn.determinant(Mw)
			if args.verbose:
				print("w =", test_w, ", det(Mw) = ", det)
			if int(det) == 0:
				v = test_w
				break
			# print("test_w = ", test_w, ", det = ", det)
		if v is None:
			raise ValueError("Cannot find weight of")
	if args.verbose:
		print("Error number v = ", v)

	# Calculate syndrone poly s(x)
	step.show("Calculate syndrone poly s(x)", verbose=args.verbose)
	syndrones = []
	for i in range(0,2*v):
		si = r_ext(alpha_ext.power(b0+i))
		syndrones = [si] + syndrones
	sx = GFn.GFn_poly(syndrones)

	if GFn.weight(sx) == 0:
		print("No error")
		print("c_recovered = \n", r_ext)
		exit()

	if args.verbose:
		print("Syndrones")
		for i, s in enumerate(syndrones):
			print("\ts"+str(i), " = ", s)
		print("s(x) = \n", sx)


	# Calculate locator polynomial and evaluation polynomial
	if args.epoly == 'berlekamp':

		# Calculate locator polynomial
		step.show("Calculate locator polynomial", verbose=args.verbose )
		loc_poly = Berlekamp_Massey( syndrones, verbose=args.verbose )

		# Evaluation polynomial calculation: eva_poly = [s(x) * sigma(x)] % x^v
		step.show("Calculate evaluation polynomial", verbose=args.verbose)
		product_sx_sigmax = sx * loc_poly
		x_times_v = GFn.GFn_poly(1,log_ext) << v
		eva_poly = product_sx_sigmax % x_times_v
		if args.verbose:
			print("evaluation polynomial = \n", eva_poly)
			try:
				print("given evaluation polynomial = \n", given_eva)
			except NameError:
				print("No given evaluation polynomial")

	elif args.epoly == 'euclidean':
		# Calculate locator polynomial and evaluation polynomial
		step.show("Calculate locator polynomial and evaluation polynomial", verbose=args.verbose )
		loc_poly, eva_poly = Euclidean( sx, v, verbose=args.verbose)

	else:
		raise ValueError("Undefined error polynomial method")


	# Obtain error locator from locator polynomial
	step.show("Calculate error locator from locator polynomial", verbose=args.verbose)
	loc_Xs = []
	roots_power, roots = GFn.finding_roots( loc_poly, ext=log_ext, alpha=alpha_ext, method=args.findroot )

	if args.verbose:
		print("Roots of locator polynomial: ", roots)
	for i, root_power_root in enumerate(zip(roots_power, roots)):
		root_power, root = root_power_root
		loc_Xs.append(root)
		if args.verbose:
			print("\tRoots #", i, ":", root, "= alpha ^", root_power, " => X = alpha ^", q**m-1 - root_power)

	# Forney's algorithm
	loc_pair = []
	step.show("Calculate Yi", verbose=args.verbose)
	for i, X in enumerate(loc_Xs):
		w             = eva_poly(X)
		# sigma_prime   = np.polyder(loc_poly)
		sigma_prime   = loc_poly.derivative()
		sigma_prime_X = sigma_prime(X)
		Y = sigma_prime_X.inverse() * w
		loc_pair.append((X.inverse(),Y))
		if args.verbose:
			print("#", i, ": Yi = w(", X, ")/sigma'(", X, ") = ", w, "/", sigma_prime_X, " = ", Y )

	# Generating e(x) from locator pair
	step.show("Generating e(x) from locator pair", verbose=args.verbose)
	if args.verbose:
		print("loc_pair = ", loc_pair)
		try:
			print("given_loc_pair = ", given_loc_pair)
		except NameError:
			print("No given locator pair")
	# check_generalized_newtons_identities( loc_poly, loc_pair )
	recovered_e_poly = GFn.GFn_poly(0,log_ext)
	for i, loc in enumerate(loc_pair):
		err_loc, err_value = loc
		err = GFn.GFn_poly(err_value, log_ext) << err_loc.log_a()
		if args.verbose:
			print("Error #", i, ": = (", err_value, err_loc, ")\n", err)
		recovered_e_poly += err

	
	c_recovered = r_ext + recovered_e_poly
	print("c_recovered = \n", c_recovered)

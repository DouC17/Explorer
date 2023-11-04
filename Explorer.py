from collections import Counter
from itertools import product
from numpy import zeros, ones, array, random, log, sum, max, argmax, argsort, unique, intersect1d, where

from dsw.operation import Monitor, calculus_addition, calculus_multiplication, calculus_division
from dsw.operation import bit_to_number, number_to_bit, number_to_dna, dna_to_number
from dsw.graphized import obtain_vertices, obtain_latters, path_matching, calculate_intersection_score,path_matching_explorer


def encode_explorer(binary_message, bio_filter, accessor, start_index, observed_length, nucleotides=None,
               vt_length=0, shuffles=None, verbose=False):
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    quotient, dna_string, vertex_index, monitor = bit_to_number(binary_message), "", int(start_index), Monitor()
    total_state = len(quotient)  # number of symbol.
    out_degree = ""
    while quotient != "0":

        if accessor.get(vertex_index) is None:
            # print(number_to_dna(int(vertex_index), dna_length=observed_length), '该顶点未判别')
            latters = obtain_latters(current=vertex_index, observed_length=observed_length,nucleotides=nucleotides)
            A=zeros(shape= len(nucleotides), dtype=int)
            for position, latter_vertex_index in enumerate(latters):
                if bio_filter.valid(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides)):
                    # print(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides))
                    A[position] = latter_vertex_index
                else:
                    # print(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides))
                    A[position] = int(-1)                
                # print(A)
            accessor[vertex_index]=A
            # print(accessor)
        # else:
        #     print('this vertex has been used!',dna_string,len(dna_string),vertex_index,accessor[vertex_index])
        #     # quit()

        used_indices = where(accessor[vertex_index] >= 0)[0]
        out_degree += str(len(used_indices))

        #判断是否有出度为2的幂 新加入
        # if (len(used_indices)!=1) & (len(used_indices)!=2) & (len(used_indices)!=4 )& (len(used_indices)!=8):
        # if len(used_indices) not in [0,1,2,4,8]:
        #     print(number_to_dna(int(vertex_index), dna_length=observed_length,nucleotides=nucleotides),'now vertex outdegree is not 2 mi:',len(used_indices),accessor[vertex_index])
        #     quit()

        # print(out_degree)
        if len(used_indices) > 1:  # current vertex contains information.
            quotient, remainder = calculus_division(number=quotient, base=str(len(used_indices)))
            remainder = int(remainder)

            if shuffles is not None:  # shuffle remainder based on the inputted shuffles.
                remainder = argsort(shuffles[vertex_index, used_indices])[remainder]

            value = used_indices[remainder]

        elif len(used_indices) == 1:  # current vertex does not contain information.
            value = used_indices[0]

        else:  # current vertex is wrong.
            print(number_to_dna(int(vertex_index), dna_length=observed_length,nucleotides=nucleotides))
            raise ValueError("Current vertex doesn't have an out-degree, the accessor or the start vertex is wrong!")

        nucleotide, vertex_index = nucleotides[value], accessor[vertex_index][value]

        dna_string += nucleotide
        if verbose:
            if quotient != "0":
                monitor.output(total_state - len(quotient), total_state)
            else:
                monitor.output(total_state, total_state)

    if vt_length > 0:
        vt_check = set_vt(dna_string=dna_string, vt_length=vt_length, nucleotides=nucleotides)
        return dna_string,accessor, vt_check
    else:
        return dna_string, accessor,out_degree


def decode_explorer(bio_filter,observed_length,dna_string, bit_length,  accessor, start_index, nucleotides=None,
           vt_check=None, shuffles=None, verbose=False):

    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    quotient, saved_values, vertex_index, monitor = "0", [], start_index, Monitor()
    for location, nucleotide in enumerate(dna_string):

        if accessor.get(vertex_index) is None:
            # print(number_to_dna(int(vertex_index), dna_length=observed_length), '该顶点未判别')
            latters = obtain_latters(current=vertex_index, observed_length=observed_length,nucleotides=nucleotides)
            A=zeros(shape= len(nucleotides), dtype=int)
            for position, latter_vertex_index in enumerate(latters):
                if bio_filter.valid(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides)):
                    # print(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides))
                    A[position] = latter_vertex_index
                else:
                    # print(number_to_dna(latter_vertex_index, dna_length=observed_length,nucleotides=nucleotides))
                    A[position] = int(-1)                
                # print(A)
            accessor[vertex_index]=A

        # latters = obtain_latters(current=vertex_index, observed_length=observed_length, nucleotides=nucleotides)
        # A = zeros(shape=len(nucleotides), dtype=int)
        # for position, latter_vertex_index in enumerate(latters):
        #     if bio_filter.valid(number_to_dna(latter_vertex_index, dna_length=observed_length, nucleotides=nucleotides)):
        #         A[position] = latter_vertex_index
        #     else:
        #         A[position] = int(-1)
        # accessor[vertex_index] = A

        used_indices = where(accessor[vertex_index] >= 0)[0]

        if len(used_indices) > 1:  # current vertex contains information.
            used_nucleotides = [nucleotides[used_index] for used_index in used_indices]

            if nucleotide in used_nucleotides:  # check whether the DNA string is right currently.
                remainder = used_nucleotides.index(nucleotide)
            else:
                print(nucleotide)
                raise ValueError("At least one error is found in this DNA string!")

            if shuffles is not None:  # shuffle remainder based on the inputted shuffles.
                remainder = where(argsort(shuffles[vertex_index, used_indices]) == remainder)[0][0]

            saved_values.append((len(used_indices), remainder))
            vertex_index = accessor[vertex_index][nucleotides.index(nucleotide)]

        elif len(used_indices) == 1:  # current vertex does not contain information.
            used_nucleotide = nucleotides[used_indices[0]]
            if nucleotide == used_nucleotide:
                vertex_index = accessor[vertex_index][nucleotides.index(nucleotide)]
            else:
                raise ValueError("At least one error is found in this DNA string!")

        else:  # current vertex is wrong.
            raise ValueError("Current vertex doesn't have an out-degree, "
                             + "the accessor, the start vertex, or DNA string is wrong!")

        if verbose:
            monitor.output(location + 1, len(dna_string))

    if vt_check is not None:
        if vt_check != set_vt(dna_string=dna_string, vt_length=len(vt_check), nucleotides=nucleotides):
            raise ValueError("At least one error is found in this DNA string!")

    for location, (out_degree, number) in enumerate(saved_values[::-1]):
        quotient = calculus_multiplication(number=quotient, base=str(out_degree))
        quotient = calculus_addition(number=quotient, base=str(number))

    return array(number_to_bit(decimal_number=quotient, bit_length=bit_length), dtype=int),accessor


def set_vt(dna_string, vt_length, nucleotides=None):
    """
    Set Varshamov-Tenengolts-based path check string ('salt-protected') from DNA (payload) string.

    :param dna_string: DNA string encoded through SPIDER-WEB.
    :type dna_string: str

    :param vt_length: length of DNA string (path check).
    :type vt_length: int or None

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list or None

    :return: path check DNA string with required length.

    Example
        >>> from dsw import set_vt
        >>> dna_string = "TCTCTCT"
        >>> vt_length = 5
        >>> set_vt(dna_string=dna_string, vt_length=vt_length)
        'TAAGC'

    .. note::
        Reference [1] Rom R. Varshamov and Grigory M. Tenengolts (1965) Avtomat. i Telemekh

        Reference [2] Grigory Tenengolts (1984) IEEE Transactions on Information Theory

        Reference [3] William H. Press et al. (2020) Proceedings of the National Academy of Sciences

        Reference [4] A. Xavier Kohll et al. (2020) Chemical Communications
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    values = array([nucleotides.index(nucleotide) for nucleotide in dna_string])
    vt_value = sum(where((values[1:] - values[:-1]) > 0)[0]) % (len(nucleotides) ** (vt_length - 1))
    vt_flag = sum(values) % len(nucleotides)

    return nucleotides[vt_flag] + number_to_dna(decimal_number=int(vt_value), dna_length=vt_length - 1)


def repair_dna_explorer(dna_string, bio_filter, start_index, observed_length, vt_check=None, has_indel=False, nucleotides=None):

    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    location, vertex_index, index_queue = 0, start_index, -ones(shape=(len(dna_string),), dtype=int)
    split_strings, chuck_strings, index_markers, detected_count, chuck_flag, visited_times = [""], [], [], 0, False, 0
    accessor={}
    while location < len(dna_string):       

        latters = obtain_latters(current=vertex_index, observed_length=observed_length, nucleotides=nucleotides)
        A = zeros(shape=len(nucleotides), dtype=int)
        for position, latter_vertex_index in enumerate(latters):
            if bio_filter.valid(number_to_dna(latter_vertex_index, dna_length=observed_length, nucleotides=nucleotides))==True:
                A[position] = latter_vertex_index
            else:
                A[position] = int(-1)
        accessor[vertex_index] = A

        used_indices, nucleotide = where(accessor[vertex_index] >= 0)[0], dna_string[location]
        if dna_string[location] in [nucleotides[used_index] for used_index in used_indices]:
            split_strings[-1] += nucleotide
            vertex_index = accessor[vertex_index][nucleotides.index(nucleotide)]
            index_queue[location] = vertex_index
            visited_times += 1
            location += 1
        elif len(split_strings) > 0:
            detected_count += 1
            split_strings[-1] = split_strings[-1][: - observed_length + 1]
            split_strings.append("")
            vertex_index = dna_to_number(dna_string[location + 2: location + observed_length + 2], is_string=False)
            index_markers.append(index_queue[location - observed_length: location])
            chuck_strings.append(dna_string[location - observed_length + 1: location + observed_length])
            location += observed_length

    repaired_fragment_set = [set() for _ in range(len(index_markers))]
    for index, (chuck_string, index_marker) in enumerate(zip(chuck_strings, index_markers)):
        for recall, vertex_index in enumerate(index_marker[::-1]):
            record, times = path_matching_explorer(dna_string=chuck_string, observed_length=observed_length,bio_filter=bio_filter,has_indel=has_indel,
                                          previous_index=vertex_index, occur_location=observed_length - recall - 1)
            visited_times += times
            for _, fragment in record:
                if dna_string not in repaired_fragment_set[index]:
                    repaired_fragment_set[index].add(fragment)
        repaired_fragment_set[index] = list(repaired_fragment_set[index])

    repaired_results, count = set(), 1
    for fragments in repaired_fragment_set:
        count *= len(fragments)

    if count == 0:
        if vt_check is not None:
            if vt_check == set_vt(dna_string=dna_string, vt_length=len(vt_check), nucleotides=nucleotides):
                return [dna_string], (0, False, 0, visited_times)
            else:
                return [], (0, True, 0, visited_times)
        else:
            return [dna_string], (0, False, 0, visited_times)

    for fragments in product(*repaired_fragment_set):
        repaired_dna_string = ""
        for index in range(len(split_strings) - 1):
            repaired_dna_string += split_strings[index] + fragments[index]
        repaired_dna_string += split_strings[-1]
        if vt_check is not None:
            if vt_check == set_vt(dna_string=repaired_dna_string, vt_length=len(vt_check), nucleotides=nucleotides):
                repaired_results.add(repaired_dna_string)
            else:
                chuck_flag = True
        else:
            repaired_results.add(repaired_dna_string)

    return sorted(list(repaired_results)), (detected_count, chuck_flag, count, visited_times)


def find_vertices(observed_length, bio_filter, nucleotides=None, verbose=False):
    """
    Find valid vertices based on the given the biochemical constraints.

    :param observed_length: length of the DNA string in a vertex.
    :type observed_length: int

    :param bio_filter: screening operation for identifying the valid DNA string (required the given constraints).
    :type bio_filter: dsw.biofilter.DefaultBioFilter

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list

    :param verbose: need to print log.
    :type verbose: bool

    :return: available vertices.
    :rtype: numpy.ndarray

    :raise ValueError: if no valid vertices are available under the required biochemical constraints.

    Example
        >>> from dsw import LocalBioFilter, find_vertices
        >>> bio_filter = LocalBioFilter(observed_length=2, max_homopolymer_runs=2, gc_range=[0.5, 0.5])
        >>> # "1" refers to the available index of vertex, otherwise "0" refers to unavailable index of vertex.
        >>> find_vertices(observed_length=2, bio_filter=bio_filter).astype(int)
        array([0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])

    .. note::
        Reference [1] Florent Capelli and Yann Strozecki (2019) Discrete Applied Mathematics
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    vertices, monitor = zeros(shape=(int(len(nucleotides) ** observed_length),), dtype=bool), Monitor()

    if verbose:
        print("Find valid vertices in this observed length of DNA string.")

    for vertex_index in range(len(vertices)):
        dna_string = number_to_dna(decimal_number=vertex_index, dna_length=observed_length,nucleotides=nucleotides)
        vertices[vertex_index] = bio_filter.valid(dna_string=dna_string)

        if verbose:
            monitor.output(vertex_index + 1, len(vertices))

    valid_rate = sum(vertices) / len(vertices)

    if valid_rate == 0:
        raise ValueError("No vertex is collected!")

    if verbose:
        print(str(round(valid_rate * 100, 2)) + "% (" + str(sum(vertices)) + ") valid vertices are collected.")

    return vertices


def connect_valid_graph(observed_length, vertices, nucleotides=None, verbose=False):
    """
    Connect a valid graph by valid vertices.

    :param observed_length: length of the DNA string in a vertex.
    :type observed_length: int

    :param vertices: vertex accessor, in each cell, True is valid vertex and False is invalid vertex.
    :type vertices: numpy.ndarray

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list

    :param verbose: need to print log.
    :type verbose: bool

    :return: accessor of the valid graph.
    :rtype: numpy.ndarray

    :raise ValueError: if no valid vertices are available.

    Example
        >>> from numpy import array
        >>> from dsw import connect_valid_graph 
        >>> vertices = array([0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])
        >>> connect_valid_graph(observed_length=2, vertices=vertices)
        array([[-1, -1, -1, -1],
               [ 4, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1, -1, -1, -1],
               [ 4, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1]])

    .. note::
        Reference [1] Nicolaas Govert de Bruijn (1946) Indagationes Mathematicae
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    if vertices is None:
        raise ValueError("No collected vertex!")

    if verbose:
        print("Connect valid graph with valid vertices.")

    valid_rate, monitor = sum(vertices) / len(vertices), Monitor()

    if valid_rate > 0:
        accessor = -ones(shape=(int(len(nucleotides) ** observed_length), len(nucleotides)), dtype=int)

        for vertex_index in range(int(len(nucleotides) ** observed_length)):
            if vertices[vertex_index]:
                latters = obtain_latters(current=vertex_index, observed_length=observed_length)
                for position, latter_vertex_index in enumerate(latters):
                    if vertices[latter_vertex_index]:
                        accessor[vertex_index][position] = latter_vertex_index

            if verbose:
                monitor.output(vertex_index + 1, len(vertices))

        if verbose:
            print("Valid graph is created.")

        return accessor
    else:
        raise ValueError("No collected vertex!")


def connect_coding_graph(observed_length, vertices, threshold, nucleotides=None, verbose=False):
    """
    Connect a coding algorithm by valid vertices and the threshold for minimum out-degree.

    :param observed_length: length of the DNA string in a vertex.
    :type observed_length: int

    :param vertices: vertex accessor, in each cell, True is valid vertex and False is invalid vertex.
    :type vertices: numpy.ndarray

    :param threshold: threshold for minimum out-degree.
    :type threshold: int

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list

    :param verbose: need to print log.
    :type verbose: bool

    :return: coding vertices and coding accessor.
    :rtype: (numpy.ndarray, numpy.ndarray)

    :raise ValueError: if no coding graph are created because of the vertex set and/or the trimming requirement.

    Example
        >>> from numpy import array
        >>> from dsw import connect_coding_graph
        >>> vertices = array([0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])
        >>> vertices, accessor = connect_coding_graph(observed_length=2, vertices=vertices, threshold=2)
        >>> accessor
        array([[-1, -1, -1, -1],
               [ 4, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1, -1, -1, -1],
               [ 4, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1]])
        >>> vertices.astype(int)
        array([0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0])

    .. note::
        Reference [1] Nicolaas Govert de Bruijn (1946) Indagationes Mathematicae
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    times = 1

    while True:
        if verbose:
            print("Check the vertex collection requirement in round " + str(times) + ".")

        new_vertices, monitor = zeros(shape=(int(len(nucleotides) ** observed_length),), dtype=bool), Monitor()
        saved_indices = where(vertices != 0)[0]
        for current, vertex_index in enumerate(saved_indices):
            latter_indices = obtain_latters(current=vertex_index, observed_length=observed_length,nucleotides=nucleotides)
            new_vertices[vertex_index] = sum(vertices[latter_indices]) >= threshold

            if verbose:
                monitor.output(current + 1, len(saved_indices))

        changed = sum(vertices) - sum(new_vertices)

        if verbose:
            print(str(round(sum(new_vertices) / len(vertices) * 100, 2)) + "% (" + str(sum(new_vertices)) + ") "
                  + "valid vertices are saved.")

        if sum(new_vertices) < 1:
            raise ValueError("No coding graph is created!")

        if not changed:
            break

        vertices = new_vertices
        times += 1

    valid_rate = sum(vertices) / len(vertices)
    if valid_rate > 0:
        accessor = -ones(shape=(int(len(nucleotides) ** observed_length), len(nucleotides)), dtype=int)
        for vertex_index in range(int(len(nucleotides) ** observed_length)):
            if vertices[vertex_index]:
                latters = obtain_latters(current=vertex_index, observed_length=observed_length,nucleotides=nucleotides)
                for position, latter_vertex_index in enumerate(latters):
                    if vertices[latter_vertex_index]:
                        accessor[vertex_index][position] = latter_vertex_index

            if verbose:
                monitor.output(vertex_index + 1, len(vertices))

        if verbose:
            print("The coding graph is created.")

        return vertices, accessor
    else:
        raise ValueError("The coding graph cannot be created!")


def remove_nasty_arc(accessor, latter_map, iteration=0, nucleotides=None, repair_insertion=True, repair_deletion=True,
                     verbose=False):
    """
    Remove the nasty arc.

    :param accessor: accessor of the coding algorithm.
    :type accessor: numpy.ndarray

    :param latter_map: latter map of the coding algorithm.
    :type latter_map: dict

    :param iteration: current round if required.
    :type iteration: int

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list

    :param repair_insertion: need to repair insertion error.
    :type repair_insertion: bool

    :param repair_deletion: need to repair deletion error.
    :type repair_deletion: bool

    :param verbose: need to print log.
    :type verbose: bool

    :return: adjusted accessor, adjusted latter map, removed arc, and maximum intersection score.
    :rtype: (numpy.ndarray, dict, tuple, int)

    Example
        >>> from numpy import array
        >>> from dsw import accessor_to_latter_map, remove_nasty_arc
        >>> # accessor with GC-balanced
        >>> accessor = array([[-1, -1, -1, -1], [ 4, -1, -1,  7], [ 8, -1, -1, 11], [-1, -1, -1, -1], \
                              [-1,  1,  2, -1], [-1, -1, -1, -1], [-1, -1, -1, -1], [-1, 13, 14, -1], \
                              [-1,  1,  2, -1], [-1, -1, -1, -1], [-1, -1, -1, -1], [-1, 13, 14, -1], \
                              [-1, -1, -1, -1], [ 4, -1, -1,  7], [ 8, -1, -1, 11], [-1, -1, -1, -1]])
        >>> latter_map = accessor_to_latter_map(accessor)
        >>> result = remove_nasty_arc(accessor=accessor, latter_map=latter_map, iteration=0, verbose=False, \
                                      nucleotides=["A", "C", "G", "T"], repair_insertion=True, repair_deletion=True)
        >>> result[0]
        array([[-1, -1, -1, -1],
               [-1, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1,  1,  2, -1],
               [-1, -1, -1, -1],
               [-1, -1, -1, -1],
               [-1, 13, 14, -1],
               [-1, -1, -1, -1],
               [ 4, -1, -1,  7],
               [ 8, -1, -1, 11],
               [-1, -1, -1, -1]])
        >>> result[1]
        {1: [7], 2: [8, 11], 4: [1, 2], 7: [13, 14], 8: [1, 2], 11: [13, 14], 13: [4, 7], 14: [8, 11]}
        >>> result[2]
        (1, 4)
        >>> result[3]
        [16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16, 16]

    .. note::
        The graph information contained in "accessor" and "latter_map" is consistent.

        It is a gift for the follow-up investigation.
        That is, removing arc to improve the capability of the probabilistic error correction.
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    observed_length = int(log(len(accessor)) / log(len(nucleotides)))

    if verbose:
        if iteration > 0:
            print("Calculate the intersection score for each remained arc in " + str(iteration) + " round(s).")
        else:
            print("Calculate the intersection score for each remained arc.")

    scores = calculate_intersection_score(latter_map=latter_map, nucleotides=nucleotides,
                                          repair_insertion=repair_insertion, repair_deletion=repair_deletion,
                                          observed_length=observed_length, verbose=verbose)

    vertex_indices = unique(where(scores == max(scores))[0])

    former = intersect1d(obtain_vertices(accessor=accessor), vertex_indices)[0]
    former_value, latter_value = former % len(nucleotides), argmax(scores[former])
    latter = int((former * len(nucleotides) + latter_value) % (len(nucleotides) ** observed_length))

    accessor[former, latter_value] = -1
    del latter_map[former][latter_map[former].index(latter)]
    if len(latter_map[former]) == 0:
        del latter_map[former]

    scores = scores.reshape(-1)
    scores = scores[scores > 0].tolist()
    score_record = array(list(Counter(scores).items())).T
    score_record = score_record[:, argsort(score_record[0])[::-1]]

    if verbose:
        print("Current scores are:")
        print(score_record)
        print("Remove arc " + number_to_dna(int(former), dna_length=observed_length) + " -> "
              + number_to_dna(int(latter), dna_length=observed_length)
              + " with the maximum intersection score " + str(max(scores)) + ".")

    return accessor, latter_map, (former, latter), scores


def create_random_shuffles(observed_length, nucleotides=None, random_seed=None, verbose=False):
    """
    Create the shuffles for accessor through the random mechanism.

    :param observed_length: length of the DNA string in a vertex.
    :type observed_length: int

    :param nucleotides: usage of nucleotides.
    :type nucleotides: list

    :param random_seed: random seed for creating shuffles.
    :type random_seed: int

    :param verbose: need to print log.
    :type verbose: bool

    :return: shuffles for accessor.
    :rtype: numpy.ndarray

    Example
        >>> from dsw import create_random_shuffles
        >>> create_random_shuffles(observed_length=2, random_seed=2021)
        array([[3, 2, 1, 0],
               [2, 3, 1, 0],
               [3, 1, 0, 2],
               [0, 3, 1, 2],
               [3, 2, 0, 1],
               [1, 0, 3, 2],
               [0, 3, 1, 2],
               [2, 0, 1, 3],
               [2, 3, 0, 1],
               [1, 0, 3, 2],
               [2, 0, 1, 3],
               [0, 1, 3, 2],
               [2, 3, 1, 0],
               [2, 0, 3, 1],
               [0, 1, 3, 2],
               [0, 3, 2, 1]])

    .. note::
        The mapping shuffle strategy disrupts the digit-to-nucleotide mapping order,
        so it can be used as an privacy protection mechanism.

        Value 0 ~ 3 in each line shuffle only describes the relationship between progressive order and position.
        The original position is [0, 1, 2, 3].
        If the follow-up nucleotides in a vertex are ["A", "G"] when the line shuffle is [3, 2, 1, 0],
        This line shuffle can be regarded as [1, -, 0, -] for ["A", -, "G", -].

        Ths shuffle will not disclose the topology information of accessor.
    """
    if nucleotides is None:
        nucleotides = ["A", "C", "G", "T"]

    shuffles = zeros(shape=(4 ** observed_length, len(nucleotides)), dtype=int)
    shuffles[:, 1] = 1
    shuffles[:, 2] = 2
    shuffles[:, 3] = 3

    random.seed(random_seed)

    monitor = Monitor()
    for index in range(4 ** observed_length):
        card = shuffles[index]
        random.shuffle(card)
        shuffles[index] = card

        if verbose:
            monitor.output(index + 1, 4 ** observed_length)

    random.seed(None)

    return shuffles

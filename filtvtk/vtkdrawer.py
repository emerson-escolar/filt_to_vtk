import argparse
import sys



def argument_parser():
    p = argparse.ArgumentParser(description="convert filtration to vtk")
    p.add_argument("points", help = "filename to points")
    p.add_argument("simplices", help = "filename to simplices (with birth times)")
    return p


class Main(object):
    def __init__(self, args):
        self.args = args
        self.filtration = None

    def run(self):
        self.filtration = Filtration.create_from_filename_pair(self.args.points, self.args.simplices)

        drawer = VtkDrawer.create_from_filtration(self.filtration)
        drawer.output(sys.stdout)

class Filtration:
    def __init__(self):
        self.points = []
        self.simplices = []
        self.births = []

    def get_birth(self,index):
        return self.births[index]

    @staticmethod
    def create_from_filename_pair(fname_points, fname_simplices):
        with open(fname_points, 'r') as fpoints, \
             open(fname_simplices, 'r') as fsimplices:
            return Filtration.create_from_file_pair(fpoints, fsimplices)

    @staticmethod
    def create_from_file_pair(fpoints, fsimplices):
        ans = Filtration()
        ans.load_points_from_file(fpoints)
        ans.load_simplices_from_file(fsimplices)

        return ans

    def load_points_from_file(self, f):
        header = f.readline().split()
        dim = int(header[0])
        n_points = int(header[1])

        for line in f:
            data = line.split()
            if len(data) != dim:
                raise RuntimeError("Point: Invalid dimension!")
            self.points.append(tuple(float(x) for x in data))

        if len(self.points) != n_points:
            raise RuntimeWarning("Points: Incorrect in number!")
    
    def load_simplices_from_file(self, f):
        self.simplices = []
        self.births = []

        for line in f:
            if not line:
                continue

            data = line.split()
            dim = int(data[0])
            if len(data) != 1 + (dim+1) + 1:
                raise RuntimeError("Simplex: {}. Invalid data!".format(data))

            self.simplices.append( tuple(int(x) for x in data[1:-1]) )
            self.births.append( float(data[-1]) )


class VtkDrawer:
    def __init__(self, points):
        self.points = points
        self.edges = []
        self.triangles = []
        self.edge_scalars = []
        self.triangle_scalars = []

    def add_simplex(self, simplex, birth):
        if len(simplex) == 2:
            self.edges.append(simplex)
            self.edge_scalars.append(birth)
        elif len(simplex) == 3:
            self.triangles.append(simplex)
            self.triangle_scalars.append(birth)

    @staticmethod
    def create_from_filtration(filt):
        ans = VtkDrawer(filt.points)
        birth_order = 0
        for simplex in filt.simplices:
            birth_value = filt.get_birth(birth_order)
            ans.add_simplex(simplex, birth_value)
            birth_order += 1
        return ans

    def num_points(self):
        return len(self.points)

    def num_edges(self):
        return len(self.edges)

    def num_triangles(self):
        return len(self.triangles)

    def output(self, f):
        self.output_header(f)
        self.output_polygon_data(f)
        self.output_scalars(f)

    @staticmethod
    def output_header(f):
        f.write("# vtk DataFile Version 2.0\n")
        f.write("filtration\n")
        f.write("ASCII\n")

    def output_polygon_data(self, f):
        f.write("DATASET POLYDATA\n")

        f.write("POINTS {} double\n".format(self.num_points()))
        for point in self.points:
            f.write("{} {} {}\n".format(point[0], point[1], point[2]))
        f.write("\n")

        f.write("LINES {} {}\n".format(self.num_edges(), self.num_edges()*3))
        for edge in self.edges:
            f.write("2 {} {}\n".format(edge[0], edge[1]))
        f.write("\n")

        f.write("POLYGONS {} {}\n".format(self.num_triangles(), self.num_triangles()*4))
        for triangle in self.triangles:
            f.write("3 {} {} {}\n".format(triangle[0],triangle[1],triangle[2]))
        f.write("\n")

    def output_scalars(self, f):
        f.write("CELL_DATA {}\n".format(self.num_edges() + self.num_triangles()))
        f.write("SCALARS cell_births float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for x in self.edge_scalars:
            f.write("{}\n".format(x))
        for x in self.triangle_scalars:
            f.write("{}\n".format(x))




def main(args):
    Main(args).run()

if __name__ == "__main__":
    main(argument_parser().parse_args())

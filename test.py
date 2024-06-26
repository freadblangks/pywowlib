from io_utils.ctypes import *
from io_utils.struct import *
from io_utils.var_type import *
from io_utils.metaclass_hook import Structs


# Struct module allows you to create data structs declaratively.
# Unlike Python's native struct module (which is still used under the hood),
# Struct features simplified and familiar syntax close to C++ as well as type templates.
# In order to create a struct use a metaclass hook:
with Structs: # -> you can also pass alignment and endianness parameters here
    class SimplePODStruct: # -> now a struct!
        field_name: int32 # -> declare a field
        some_araay: float32[10] # -> declare an array-field with static size

    T = VarType('T') # TODO: custom subclass of VarType to support array syntax
    Tx = VarType('Tx')
    class TemplatedStruct:
        variable_type_field: T
        variable_array_length: float32[Tx]

    # Now we can use this template.
    # Specify template parameters and use as final struct.
    # % operator is used to specify template arguments
    SpecifiedStruct = TemplatedStruct % {'T': int32, 'Tx': 10}

    s = SpecifiedStruct()
    # s.read(f)

    #print(len(s.variable_array_length))
    # >>> 10
    #print(type(s.variable_array_length))
    # >>> list # initialized Python equivalent type, bounds check is performed on writing

    s.variable_array_length = [x for x in range(0, 10)]
    # s.write(f)

    # It is also possible to nest templated structs and propagate template arguments further.

    class OneArgumentTemplate:
        a: T

    Ty = VarType('Ty')
    class NestedTemplatedStruct:
        a: TemplatedStruct % {'T': Ty, 'Tx': 100}
        b: OneArgumentTemplate % Ty # if a template only has one argument, you can omit the argument name

    s = (NestedTemplatedStruct % (OneArgumentTemplate % float32))() # nested template specialization
    # and let's finally print the internal structure of this type Frankenstein

    #print(s._struct_token_string)
    # >>> f100ff

    # These token strings are evaluated for every Struct with complete template specialization
    # or non-template Struct. Internally a cached Python struct object will be created.

    # The Python type representation of the Struct.
    # If you instantiate a Struct, the resulted instance will contain a tree structure of objects,
    # which corresponds to the specified layout.
    # In case the Struct is plain old data (POD), NamedTuple will be used for hosting substructs.
    # In case the Struct is not POD, meaning it also defines supplementary non-layout members or methods
    # they will remain in the created object.
    # This behavior in the future as well as performing or not performing bounds and typechecks on use
    # will be parameterizable.


# Test coverage
T = VarType('T')
Ty = VarType('Ty')

with Structs:

    # simple non templated POD struct
    class StructD:
        a: int32
        b: float32
        c: char[10]

    # since StructD is simple, we can evaluate its struct token right away
    print("StructD:", StructD._struct_token_string)
    assert(StructD._struct_token_string == 'if10s')

    class StructB:
        a: int32
        b: T

    # StructB defines one template parameter
    # thus, its token string and size cannot be evaluated until template parameters are specified
    print("StructB:", StructB._struct_token_string)
    assert(StructB._struct_token_string is None)

    class StructA:
        a: StructB % {'T': char[10]}


    # nested array test
    class NestedArrayTest:
        a: float32[10][10]

    print("NestedArrayTest:", NestedArrayTest._struct_token_string)
    assert(NestedArrayTest._struct_token_string == '100f')

    # array of structs
    class ArrayOfStructs:
        a: NestedArrayTest[2][2]


    print("ArrayOfStructs:", ArrayOfStructs._struct_token_string)
    assert (ArrayOfStructs._struct_token_string == '100f100f100f100f')

    # array templated type
    class ArrayTemplatedType:
        a: T[10][10] # TODO: custom VarType to support T[x][x]... syntax

    array_templated_type_spec = ArrayTemplatedType % int32

    print(array_templated_type_spec.__name__, array_templated_type_spec._struct_token_string)
    assert (array_templated_type_spec._struct_token_string == '100i')

    # forwarding templated types through another nested structure
    class ArrayTypeArgumentForwardTest:
        a: ArrayTemplatedType % {'T': Ty}


    ArrayTypeArgumentForwardTest_spec = ArrayTypeArgumentForwardTest % {'Ty': float32}
    print(ArrayTypeArgumentForwardTest_spec.__name__, ArrayTypeArgumentForwardTest_spec._struct_token_string)
    assert(ArrayTypeArgumentForwardTest_spec._struct_token_string == '100f')

    # nesting this spec into another struct
    class NestedSpec:
        a: ArrayTypeArgumentForwardTest_spec
        b: ArrayTypeArgumentForwardTest_spec

    print(NestedSpec.__name__, NestedSpec._struct_token_string)

    # fully templated arrays with both type and length using template arguments
    class ComplexTemplatedArrayStruct:
        a: T[Tx]
        b: T[10]
        c: int32[Tx]

    try:
        ComplexTemplatedArrayStruct_spec = ComplexTemplatedArrayStruct % int32
    except TypeError:
        pass
        # This needs to error, as we provided just 1 template argument out of 2 required
    else:
        assert False

    ComplexTemplatedArrayStruct_spec = ComplexTemplatedArrayStruct % {'T': int32, 'Tx': 2}
    print(ComplexTemplatedArrayStruct_spec.__name__, ComplexTemplatedArrayStruct_spec._struct_token_string)
    assert(ComplexTemplatedArrayStruct_spec._struct_token_string == '2i10i2i')

    # trying to nest this into a partial specification

    try:
        class ComplexTemplatedArrayStructParent:
            # first, we use an already specified struct
            a: ComplexTemplatedArrayStruct_spec

            # second, we use a partial invalid specification
            b: ComplexTemplatedArrayStruct % {'T': int32}
    except StructError:
        # we are supposed to error here, as field b contains an unspecified type
        pass
    else:
        assert False

    # doing a second incorrect attempt, now specifying an array length with inappropriate type
    try:
        class ComplexTemplatedArrayStructParent:
            # first, we use an already specified struct
            a: ComplexTemplatedArrayStruct_spec

            # second, we use a partial invalid specification
            b: ComplexTemplatedArrayStruct % {'T': int32, 'Tx': float32}
    except TypeError:
        # erroring here, as array length can't be represented by float
        pass
    else:
        assert(False)

    # a correct attempt, finally
    class SomeSimpleTemplatedStruct:
        a: T

    class ComplexTemplatedArrayStructParent:
        # first, we use an already specified struct
        a: ComplexTemplatedArrayStruct_spec

        # second, we use a partial invalid specification
        b: ComplexTemplatedArrayStruct % {'T': Ty, 'Tx': 2}

    # now specifying and testing
    ComplexTemplatedArrayStructParent_spec = ComplexTemplatedArrayStructParent % (SomeSimpleTemplatedStruct % int32)
    print(ComplexTemplatedArrayStructParent_spec.__name__, ComplexTemplatedArrayStructParent_spec._struct_token_string)






"""
class LogicProposal:
    a: int32
    _: Conditional(
          If(lambda ctx: ctx.globals.wow_version >= WoWVersions.WOTLK,
          {
              b: int32
          }),
          Elif(lambda ctx: ctx.self.a == 1,
          {
              b: float32
          }),
          Else
          ({
              b: double
          })
       )
"""
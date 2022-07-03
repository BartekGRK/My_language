from llvmlite import ir
import llvmlite.binding as llvm
from antlr4 import *
from grammar.BaLangLexer import BaLangLexer
from grammar.BaLangVisitor import BaLangVisitor
from grammar.BaLangParser import BaLangParser
from random import randint


class IRgen(BaLangVisitor):

    def __init__(self):
        self.llvm = llvm
        self.llvm.initialize()
        self.llvm.initialize_native_target()
        self.llvm.initialize_native_asmprinter()
        self.builder = None
        self.module = None
        self.printf = None
        self.scanf = None
        self.locals = {}
        self.globals = {}
        self.functions = {}
        self.FlagIf = False
        self.LocalsIf = {}

    def root(self, node):
        self.module = ir.Module(name=__file__)
        self.module.triple = self.llvm.get_default_triple()
        func_type = ir.FunctionType(ir.IntType(32), [], False)
        base_func = ir.Function(self.module, func_type, name="main")
        block = base_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf = printf
        scantr_ty = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [scantr_ty], var_arg=True)
        scanf = ir.Function(self.module, scanf_ty, name="scanf")
        self.scanf = scanf

        self.visit(node)

        self.builder.ret(ir.Constant(ir.IntType(32), 0))

        return self.module

    def visitNumber(self, ctx: BaLangParser.NumberContext):
        return ir.Constant(ir.IntType(32), int(ctx.getText()))

    def visitDouble(self, ctx: BaLangParser.DoubleContext):
        return ir.Constant(ir.DoubleType(), float(ctx.getText()))

    def visitVar(self, ctx: BaLangParser.VarContext):
        name = ctx.getText()
        if not name in self.locals:
            raise Exception("Missing variable \"%s\" in line: " % (name, ctx.name.line))
        var = self.locals[name]
        return self.builder.load(var)

    def visitString(self, ctx: BaLangParser.StringContext):
        return ir.Constant(ir.ArrayType(ir.IntType(8),len(ctx.getText())), ctx.getText())

    def visitExpression(self, ctx: BaLangParser.ExpressionContext):
        op = ctx.op.type
        left = self.visit(ctx.left)
        right = self.visit(ctx.right)

        if left.type != right.type:
            # if isinstance(left.type, ir.IntType) and isinstance(right.type, ir.DoubleType):
            #     left = self.builder.uitofp(left, ir.DoubleType())
            # elif isinstance(right.type, ir.IntType) and isinstance(left.type, ir.DoubleType):
            #     right = self.builder.uitofp(right, ir.DoubleType())
            # else:
            raise Exception("Operation with different types in line %s" % ctx.op.line)

        if isinstance(left.type, ir.IntType):
            if op == BaLangLexer.ADD:
                return self.builder.add(left, right)
            elif op == BaLangLexer.SUB:
                return self.builder.sub(left, right)

        elif isinstance(left.type, ir.DoubleType):
            if op == BaLangLexer.ADD:
                return self.builder.fadd(left, right)
            elif op == BaLangLexer.SUB:
                return self.builder.fsub(left, right) 

        raise Exception("Unsuported types in expression")

        ptr = self.builder.alloca(decltype)
        self.locals[ctx.name.text] = ptr

    def visitDeclare(self, ctx: BaLangParser.DeclareContext):
        value = self.visit(ctx.value)

        if ctx.vartype.text == "D":
            decltype = ir.DoubleType()
            ptr = self.builder.alloca(value.type)
            self.builder.store(value, ptr)
            self.locals[ctx.name.text] = ptr
        elif ctx.vartype.text == "I":
            decltype = ir.IntType(32)
            ptr = self.builder.alloca(value.type)
            self.builder.store(value, ptr)

            
            if self.FlagIf == True:
                self.LocalsIf[ctx.name.text] = ptr
            else:
                self.locals[ctx.name.text] = ptr

            
        # if value.type != decltype :
        #      raise Exception("cannot assign difrent types in line",ctx.vartype.line)

        if ctx.vartype.text == "S":
            decltype = ir.ArrayType(ir.IntType(8),len(ctx.getText()))            
            # ptr = self.builder.alloca(value.type)
            self.napis = ctx.getText().split("\"")[1]
            self.locals[ctx.name.text] = value

    def Stringprint(self, value):
        arg = self.napis #przyjmujemy napis
        fmt = ("%s\n\0" % arg)
        c_str_val = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8"))) #tworzymy const I8 o dlugosci napisu

        global_fmt = ir.GlobalVariable(self.module, c_str_val.type, name="str."+str(randint(0, 100))) #tworzony globalny napis

        # c_str = self.builder.alloca(c_str_val.type) #creation of the allocation of the %".2" variable
        global_fmt.linkage = 'private'
        global_fmt.global_constant = True
        global_fmt.initializer = c_str_val
        # self.builder.store(c_str_val, c_str) #store as defined on the next line below %".2"

        voidptr_ty = ir.IntType(8).as_pointer() 
        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty) #creates the %".4" variable with the point pointing to the fstr
        self.builder.call(self.printf, [fmt_arg]) #We are calling the prinf function with the fmt and arg and returning the value as defiend on the next line

    def readStringprint(self, value):
        fmt = "%s \n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                            bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(
            self.module, c_fmt.type, name="fstr"+str(randint(0, 100000)))
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        voidptr_ty = ir.IntType(8).as_pointer()
        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

        self.builder.call(self.printf, [fmt_arg, self.builder.load(value)])

    def visitPrinting(self, ctx: BaLangParser.PrintingContext):
        name = ctx.name.text
        # self.Stringprint()
        if not name in self.locals:
            raise Exception("Variable \"%s\" in line: %s does not exist" % (name, ctx.name.line))
        

        if self.FlagIf:
            value = self.LocalsIf[name]
        else:
            value = self.locals[name]
        
        if isinstance (value.type, ir.ArrayType):
            self.Stringprint(value)
            return self.visitChildren(ctx)

        voidptr_ty = ir.IntType(8).as_pointer()

        if isinstance(value.type.pointee, ir.IntType):
            fmt = "%i \n\0"
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(
                self.module, c_fmt.type, name="fstr"+str(randint(0, 100000)))
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
            fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

            self.builder.call(self.printf, [fmt_arg, self.builder.load(value)])

            return self.visitChildren(ctx)
        if isinstance(value.type.pointee, ir.DoubleType):
            fmt = "%f \n\0"
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(
                self.module, c_fmt.type, name="fstr"+str(randint(0, 100000)))
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
            fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

            self.builder.call(self.printf, [fmt_arg, self.builder.load(value)])

            return self.visitChildren(ctx)
        else:
            self.readStringprint(value)
            
    def ReadIntDouble(self,var_type,ctx):

        if str(var_type) == "D":
            ptr = self.builder.alloca(ir.DoubleType())
        else:
            ptr = self.builder.alloca(ir.IntType(32))

        name = ctx.name.text
        self.locals[name] = ptr

        voidptr_ty = ir.IntType(8).as_pointer()
        fmt = "%i\0"
        if isinstance(ptr.type.pointee, ir.DoubleType):
            fmt = "%lf\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                            bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(
            self.module, c_fmt.type, name="fstr"+str(randint(0, 100000)))
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)
        self.builder.call(self.scanf, [fmt_arg, ptr])
    
    def visitReading(self, ctx: BaLangParser.ReadingContext):
        var_type = ctx.getChild(0)
        
       
        # if not name in self.locals:
        #     raise Exception("missing variable ", name)
        if str(var_type) == 'S':
            decltype = ir.ArrayType(ir.IntType(8),20)            
            ptr = self.builder.alloca(decltype)
            name = ctx.name.text
            self.locals[name] = ptr
            voidptr_ty = ir.IntType(8).as_pointer()
            fmt = "%s\0"
            c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                                bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(
                self.module, c_fmt.type, name="str"+str(randint(0, 10)))
            global_fmt.linkage = 'private'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
            fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)
            self.builder.call(self.scanf, [fmt_arg, ptr])
        elif str(var_type) == 'I' or 'D':
            self.ReadIntDouble(var_type,ctx)
        
    def visitIf(self, ctx: BaLangParser.ExpressionContext):
        op = ctx.ifoperator.op.text
     
        left = ctx.ifoperator.left.text
        left = self.locals[ctx.ifoperator.left.text]        
        # right = ctx.ifoperator.right.text       
        rightvalue = self.visit(ctx.ifoperator.right)
        leftvalue = self.builder.load(left)

        loophead = self.builder.append_basic_block('IF')
        loopbody = self.builder.append_basic_block('IF_body')
        loopend = self.builder.append_basic_block('EndIF')

        self.builder.branch(loophead)
        self.builder.position_at_end(loophead)

        l_r = self.builder.icmp_signed(op, leftvalue, rightvalue)
        self.builder.cbranch(l_r, loopbody, loopend)
        # self.builder.branch(loopend)
        self.builder.position_at_end(loopbody)
        self.FlagIf = True
        self.visitChildren(ctx)
        self.builder.branch(loopend)
        self.FlagIf = False
        self.builder.position_at_end(loopend)
        #Test nie do konca działający
        # with self.builder.if_then(l_r) as bbend:
        #     bb_then = self.builder.basic_block
        #     self.FlagIf = bb_then
        #     self.visitChildren(ctx)
        #     self.FlagIf = None

    def visitDofunction(self,ctx: BaLangParser.ExpressionContext):
        double = ir.DoubleType()
        func_type = ir.FunctionType(ir.IntType(32), [], False)
        func = ir.Function(self.module, func_type, name="funkcja")
        block = func.append_basic_block(name="entry")
        add = self.visitChildren(ctx)
        self.builder = ir.IRBuilder(block)
        self.builder.ret(ir.Constant(ir.IntType(32), 0))

       
        
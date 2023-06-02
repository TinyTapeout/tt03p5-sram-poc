import random
from typing import Callable
import cocotb
from cocotb.clock import Clock
from cocotb.binary import BinaryValue
from cocotb.triggers import ClockCycles


# TODO use custom range(start+offset,end,by) to wrap address space end+1/by times
MEM_SIZE = 0x80
MAX_ADDR = MEM_SIZE - 1
DATA_WIDTH = 8
DATA_0 = 0x00
DATA_1 = 0xff
DATA_X = BinaryValue('X', n_bits=DATA_WIDTH)


def randbytes(n: int) -> bytearray:
    bytes = []
    for i in range(n):
        b = random.randrange(2**DATA_WIDTH)
        bytes.append(b)
        #dut._log.info(f"random({i}) = {b}")
    return bytearray(bytes)


async def fill(dut,
        start: int = 0,
        end: int = MAX_ADDR,
        by: int = 1,
        offset: int = 0,
        fillfunc: Callable[[int], int] = lambda a: DATA_0) -> None:

    dut.we.value = 1
    for a in range(start+offset,end+1,by):
        d = fillfunc(a)
        dut.data_in.value = d
        dut.addr.value = a
        await ClockCycles(dut.clk, 1)
        #dut._log.info(f"fill a={a} d={d}")

    dut.we.value = 0
    dut.data_in.value = DATA_X


async def read(dut,
        start: int = 0,
        end: int = MAX_ADDR,
        by: int = 1,
        offset: int = 0,
        pipeline: bool = False,
        compute: Callable[[int,BinaryValue], bool] = lambda a,v: DATA_0) -> None:

    dut.we.value = 0
    dut.data_in.value = DATA_X

    ticks = 1 if pipeline else 2
    #dut._log.info(f"read(start={start}, end={end}, by={by}, offset={offset}, pipeline={pipeline}) pipeline={pipeline} ticks={ticks}")

    lasta = None
    for a in range(start+offset,end+1,by):
        dut.addr.value = a
        #dut._log.info(f"a={a}")
        if ticks == 2 and lasta is not None:	# !pipeline
            expect = compute(lasta, dut.data_out.value)
            #dut._log.info(f"a={lasta} d={dut.data_out.value} expect={expect}")
            assert dut.data_out.value == expect, f"read(by={by}, offset={offset}, pipeline={pipeline}) a={lasta} d={dut.data_out.value} expect={expect}"
        await ClockCycles(dut.clk, ticks)
        if ticks == 1 and lasta is not None:	# pipeline
            expect = compute(lasta, dut.data_out.value)
            #dut._log.info(f"a={lasta} d={dut.data_out.value} expect={expect}")
            assert dut.data_out.value == expect, f"read(by={by}, offset={offset}, pipeline={pipeline}) a={lasta} d={dut.data_out.value} expect={expect}"
        lasta = a

    if lasta is not None:
        await ClockCycles(dut.clk, 1)
        expect = compute(lasta, dut.data_out.value)
        assert dut.data_out.value == expect, f"read(by={by}, offset={offset}, pipeline={pipeline}) a={lasta} d={dut.data_out.value} expect={expect}"


@cocotb.test()
async def test_sram_poc(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("ena")
    dut.ena.value = 1

    dut._log.info("reset")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # All the bidirectional ports are used for the data_in signal, so they should be inputs
    assert int(dut.bidirectional_is_output.value) == 0

    dut._log.info("write 4 bytes to addresses 8, 9, 10, 11")
    dut.addr.value = 8
    dut.data_in.value = 0x55
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut.addr.value = 9
    dut.data_in.value = 0x66
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut.addr.value = 10
    dut.data_in.value = 0x77
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut.addr.value = 11
    dut.data_in.value = 0x88
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("read back the bytes and verify they are correct")
    dut.data_in.value = 0  # DATA_X
    dut.addr.value = 8
    dut.we.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x55

    dut.addr.value = 9
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x66

    dut.addr.value = 10
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x77

    dut.addr.value = 11
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x88

    dut._log.info("write a byte at address 12")
    dut.addr.value = 12
    dut.data_in.value = 0x99
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("overwrite the byte at address 10")
    dut.addr.value = 10
    dut.data_in.value = 0xaa
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("read back the bytes and verify they are correct")
    dut.data_in.value = 0  # DATA_X
    dut.we.value = 0
    dut.addr.value = 12
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x99

    dut.addr.value = 10
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xaa

    dut.addr.value = 8
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0x55


    dut._log.info("read pipeline back-to-back bytes and verify they are correct")
    dut.data_in.value = DATA_X
    dut.we.value = 0

    dut.addr.value = 8
    await ClockCycles(dut.clk, 1)

    dut.addr.value = 9
    await ClockCycles(dut.clk, 1)
    #dut._log.info("addr(08) = {:x}".format(int(dut.data_out.value)))
    assert int(dut.data_out.value) == 0x55, f"addr(08) != 0x55"

    dut.addr.value = 10
    await ClockCycles(dut.clk, 1)
    #dut._log.info("addr(09) = {:x}".format(int(dut.data_out.value)))
    assert int(dut.data_out.value) == 0x66, f"addr(09) != 0x66"

    dut.addr.value = 11
    await ClockCycles(dut.clk, 1)
    #dut._log.info("addr(10) = {:x}".format(int(dut.data_out.value)))
    assert int(dut.data_out.value) == 0xaa, f"addr(10) != 0xaa"

    dut.addr.value = 8
    await ClockCycles(dut.clk, 1)
    #dut._log.info("addr(11) = {:x}".format(int(dut.data_out.value)))
    assert int(dut.data_out.value) == 0x88, f"addr(11) != 0x88"

    dut.addr.value = 9
    await ClockCycles(dut.clk, 1)
    assert int(dut.data_out.value) == 0x55, f"addr(08) != 0x55"

    dut.addr.value = 10
    await ClockCycles(dut.clk, 1)
    assert int(dut.data_out.value) == 0x66, f"addr(09) != 0x66"

    dut.addr.value = 11
    await ClockCycles(dut.clk, 1)
    assert int(dut.data_out.value) == 0xaa, f"addr(10) != 0xaa"

    dut.addr.value = 0
    await ClockCycles(dut.clk, 1)
    assert int(dut.data_out.value) == 0x88, f"addr(11) != 0x88"

    INTERVAL = 100
    for pipeline in [False, True]:
        for by in [1,2,3,4,5,6,7,8]:	# stride
            for offset in [0,1,2,3]:	# offset at start
                # Zero
                await ClockCycles(dut.clk, INTERVAL)
                await fill(dut, fillfunc=lambda a: DATA_0)
                await ClockCycles(dut.clk, INTERVAL)
                await read(dut, by=by, offset=offset, pipeline=pipeline, compute=lambda a,v: DATA_0)

                # AllOnes
                await ClockCycles(dut.clk, INTERVAL)
                await fill(dut, fillfunc=lambda a: DATA_1)
                await ClockCycles(dut.clk, INTERVAL)
                await read(dut, by=by, offset=offset, pipeline=pipeline, compute=lambda a,v: DATA_1)

                # Identity (data value == address value)
                await ClockCycles(dut.clk, INTERVAL)
                await fill(dut, fillfunc=lambda a: a & DATA_1)
                await ClockCycles(dut.clk, INTERVAL)
                await read(dut, by=by, offset=offset, pipeline=pipeline, compute=lambda a,v: a & DATA_1)

                # Random (data)
                data = randbytes(MAX_ADDR)
                def compute(a: int, v: BinaryValue) -> int:
                    i = a % MAX_ADDR
                    return data[i]
                def fillfunc(a: int) -> int:
                    return compute(a, None)
                await ClockCycles(dut.clk, INTERVAL)
                await fill(dut, fillfunc=fillfunc)
                await ClockCycles(dut.clk, INTERVAL)
                await read(dut, by=by, offset=offset, pipeline=pipeline, compute=compute)


    # TODO Random access

    dut._log.info("all good!")

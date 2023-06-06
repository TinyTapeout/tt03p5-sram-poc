import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_sram_poc(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    dut._log.info("ena")
    dut.ena.value = 1
    dut.data_in.value = 0
    dut.bank_sel.value = 0

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
    dut.data_in.value = 0
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
    dut.data_in.value = 0
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

    dut._log.info("Switch to bank 3 and write a byte at addresses 10, 11")
    dut.data_in.value = 3
    dut.bank_sel.value = 1
    await ClockCycles(dut.clk, 1)

    dut.bank_sel.value = 0
    dut.addr.value = 10
    dut.data_in.value = 0xbb
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut.bank_sel.value = 0
    dut.addr.value = 11
    dut.data_in.value = 0xcc
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("read back the bytes and verify they are correct")
    dut.data_in.value = 0
    dut.addr.value = 10
    dut.we.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xbb
    
    dut._log.info("Switch to bank 16 and write a byte at addresses 10, 11")
    dut.data_in.value = 16
    dut.bank_sel.value = 1
    await ClockCycles(dut.clk, 1)

    dut.bank_sel.value = 0
    dut.addr.value = 10
    dut.data_in.value = 0x10
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut.bank_sel.value = 0
    dut.addr.value = 11
    dut.data_in.value = 0x11
    dut.we.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Switch to bank 0 and verify the byte at address 10 is still correct")

    dut.data_in.value = 0
    dut.bank_sel.value = 1
    dut.we.value = 0
    await ClockCycles(dut.clk, 1)

    dut.bank_sel.value = 0
    dut.addr.value = 10
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xaa

    dut._log.info("Bank select and read back the byte at addresses 11, 10")
    dut.data_in.value = 3
    dut.bank_sel.value = 1
    dut.addr.value = 11
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xcc

    dut.bank_sel.value = 0
    dut.data_in.value = 0
    dut.addr.value = 10
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xbb

    dut._log.info("Chaning the bank while bank_sel is high and verify the data")

    dut.data_in.value = 0
    dut.bank_sel.value = 1
    dut.addr.value = 10
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xaa

    dut.data_in.value = 3
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xbb

    dut.data_in.value = 0
    await ClockCycles(dut.clk, 2)
    assert int(dut.data_out.value) == 0xaa

    dut._log.info("all good!")

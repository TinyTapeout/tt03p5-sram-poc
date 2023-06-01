`default_nettype none
`timescale 1ns/1ps

/*
this testbench just instantiates the module and makes some convenient wires
that can be driven / tested by the cocotb test.py
*/

module tb (
    // testbench is controlled by test.py
    input clk,
    input rst_n,
    input ena,
    input [6:0] addr,
    input we,
    input [7:0] data_in,
    output [7:0] bidirectional_is_output,
    output [7:0] data_out
   );

    wire ram_clk0;
    wire ram_csb0;
    wire ram_web0;
    wire [3:0] ram_wmask0;
    wire [8:0] ram_addr0;
    wire [31:0] ram_din0;
    wire [31:0] ram_dout0;

    // this part dumps the trace to a vcd file that can be viewed with GTKWave
    initial begin
        $dumpfile ("tb.vcd");
        $dumpvars (0, tb);
        #1;
    end

    sky130_sram_2kbyte_1rw1r_32x512_8 sram(
        .clk0(ram_clk0),
        .csb0(ram_csb0),
        .web0(ram_web0),
        .wmask0(ram_wmask0),
        .addr0(ram_addr0),
        .din0(ram_din0),
        .dout0(ram_dout0),
        .clk1(0),
        .csb1(0),
        .addr1(0)
    );

    // instantiate the DUT
    tt_um_urish_sram_poc sramctrl(
        `ifdef GL_TEST
            .vccd1( 1'b1),
            .vssd1( 1'b0),
        `endif
        .ui_in  ({we, addr}),
        .uo_out (data_out),
        .uio_in (data_in),
        .uio_oe (bidirectional_is_output),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n),

        .ram_clk0 (ram_clk0),
        .ram_csb0 (ram_csb0),
        .ram_web0 (ram_web0),
        .ram_wmask0 (ram_wmask0),
        .ram_addr0 (ram_addr0),
        .ram_din0 (ram_din0),
        .ram_dout0 (ram_dout0)
    );

endmodule
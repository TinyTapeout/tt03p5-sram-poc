`define default_netname none

module tt_um_urish_sram_poc (
  input  wire [7:0] ui_in,   // Dedicated inputs
  output wire [7:0] uo_out,  // Dedicated outputs
  input  wire [7:0] uio_in,  // IOs: Input path
  output wire [7:0] uio_out, // IOs: Output path
  output wire [7:0] uio_oe,  // IOs: Enable path (active high: 0=input, 1=output)
  input  wire       ena,
  input  wire       clk,
  input  wire       rst_n,

  // RAM interface: 1rw
  output ram_clk0,
  output ram_csb0,       // chip select, active low
  output ram_web0,       // write enable, active low
  output [3:0] ram_wmask0,   // write mask
  output [8:0] ram_addr0,    // address (either 8 or 9 bit, depending on RAM size)
  output [31:0] ram_din0,  // input data
  input  [31:0] ram_dout0    // output data
);

  reg [2:0] addr_high_reg;
  wire bank_select = ui_in[6];
  wire [5:0] addr_low = ui_in[5:0];
  wire [2:0] addr_high_in = uio_in[2:0];
  wire [8:0] addr = {bank_select ? addr_high_in : addr_high_reg, addr_low};
  wire [1:0] byte_index = ui_in[1:0];
  
  assign uio_oe = 8'b0; // All bidirectional IOs are inputs
  assign uio_out = 8'b0;

  wire WE = ui_in[7] && !bank_select;
  wire WE0 = WE && (byte_index == 0);
  wire WE1 = WE && (byte_index == 1);
  wire WE2 = WE && (byte_index == 2);
  wire WE3 = WE && (byte_index == 3);

  wire [4:0] bit_index = {byte_index, 3'b000};
  assign ram_din0 = {24'b0, uio_in} << bit_index;
  reg  [4:0] out_bit_index;
  assign uo_out = ram_dout0[out_bit_index +: 8];

  assign ram_clk0 = clk;
  assign ram_csb0 = !rst_n;
  assign ram_web0 = !WE;
  assign ram_wmask0 = {WE3, WE2, WE1, WE0};
  assign ram_addr0 = {4'b0, addr[6:2]};

  always @(posedge clk)
  begin
    if(rst_n) begin
      out_bit_index <= bit_index;
      addr_high_reg <= bank_select ? addr_high_in : addr_high_reg;
    end else begin
      out_bit_index <= 0;
      addr_high_reg <= 0;
    end
  end

endmodule

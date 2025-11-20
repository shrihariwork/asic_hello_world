// 8-bit Up/Down Counter with Reset and Enable
//
// Inputs:
//  clk: System Clock
//  rst_n: Active Low Asynchronous Reset
//  enable: Active High Enable
//  up_down: 1 = Up, 0 = Down
//
// Outputs:
//  count: 8-bit Counter Output

module counter (
    input wire clk,
    input wire rst_n,
    input wire enable,
    input wire up_down,
    output reg [7:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'b0;
        end else if (enable) begin
            if (up_down) begin
                count <= count + 1;
            end else begin
                count <= count - 1;
            end
        end
    end

endmodule

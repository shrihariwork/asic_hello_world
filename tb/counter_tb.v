`timescale 1ns / 1ps

module counter_tb;

    // Inputs
    reg clk;
    reg rst_n;
    reg enable;
    reg up_down;

    // Outputs
    wire [7:0] count;

    // Instantiate the Unit Under Test (UUT)
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .up_down(up_down),
        .count(count)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 100MHz clock
    end

    initial begin
        // Initialize Inputs
        rst_n = 0;
        enable = 0;
        up_down = 1;

        // Wait 100 ns for global reset to finish
        #100;
        
        // Release Reset
        rst_n = 1;
        #20;

        // Test 1: Count Up
        $display("Test 1: Count Up");
        enable = 1;
        up_down = 1;
        #200;

        // Test 2: Count Down
        $display("Test 2: Count Down");
        up_down = 0;
        #200;

        // Test 3: Disable
        $display("Test 3: Disable");
        enable = 0;
        #100;

        // Test 4: Reset during operation
        $display("Test 4: Reset during operation");
        enable = 1;
        #50;
        rst_n = 0;
        #20;
        rst_n = 1;
        #50;

        $display("Simulation Finished");
        $finish;
    end
    
    // Optional: Dump waves
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

endmodule

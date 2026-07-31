class CalculatorTest {

    @Test
    fun `adds two numbers`() {
        val calculator = Calculator()

        val result = calculator.add(2, 3)

        assertThat(result).isEqualTo(5)
    }
}

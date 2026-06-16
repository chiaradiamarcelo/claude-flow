class InterestPolicyTest {

    @Test
    fun rounds_the_monthly_rate_to_four_decimals() {
        val policy = InterestPolicy(annualRate = 0.05)

        val rate = policy.callPrivate("monthlyRate")

        assertThat(rate).isEqualTo(0.0042)
    }
}

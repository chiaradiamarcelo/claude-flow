class CalculateInterestTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var calculateInterest: CalculateInterest

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        calculateInterest = CalculateInterest(accounts)
    }

    @Test
    fun returns_the_interest_accrued_on_the_balance() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 100))

        val interest = calculateInterest.execute(ACCOUNT_ID)

        assertThat(interest).isCloseTo(33.33, within(0.01))
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}

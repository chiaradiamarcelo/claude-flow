class CountActiveAccountsTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var countActiveAccounts: CountActiveAccounts

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        countActiveAccounts = CountActiveAccounts(accounts)
    }

    @Test
    fun counts_only_the_active_accounts() {
        accounts.save(BankAccount("ACC-1", balance = 0, active = true))
        accounts.save(BankAccount("ACC-2", balance = 0, active = false))

        val count = countActiveAccounts.execute()

        assertThat(count).isEqualTo(1)
    }
}

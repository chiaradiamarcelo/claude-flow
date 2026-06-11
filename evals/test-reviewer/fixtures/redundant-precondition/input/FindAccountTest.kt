class FindAccountTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var findAccount: FindAccount

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        findAccount = FindAccount(accounts)
    }

    @Test
    fun returns_the_account_when_it_exists() {
        accounts.save(BankAccount(ACCOUNT_ID, balance = 50))

        val found = findAccount.execute(ACCOUNT_ID)

        assertThat(found).isNotNull()
        assertThat(found!!.balance).isEqualTo(50)
    }

    companion object {
        private const val ACCOUNT_ID = "ACC-1"
    }
}

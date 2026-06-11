class ListOpenAccountsTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var listOpenAccounts: ListOpenAccounts

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        listOpenAccounts = ListOpenAccounts(accounts)
    }

    @Test
    fun returns_the_ids_of_the_open_accounts() {
        accounts.save(BankAccount("ACC-1", balance = 0, open = true))
        accounts.save(BankAccount("ACC-2", balance = 0, open = true))

        val ids = listOpenAccounts.execute()

        assertThat(ids).contains("ACC-1", "ACC-2")
    }
}

class ListOwnerAccountsTest {

    private lateinit var accounts: FakeAccountRepository
    private lateinit var listOwnerAccounts: ListOwnerAccounts

    @BeforeEach
    fun setUp() {
        accounts = FakeAccountRepository()
        listOwnerAccounts = ListOwnerAccounts(accounts)
    }

    @Test
    fun returns_the_accounts_belonging_to_the_owner() {
        accounts.save(accountRow("ACC-1"))

        val found = listOwnerAccounts.execute(OWNER_ID).find { it.ownerId == OWNER_ID }

        assertThat(found).isNotNull()
    }

    private fun accountRow(id: String) = BankAccount(id, ownerId = OWNER_ID, balance = 0)

    companion object {
        private const val OWNER_ID = "OWNER-1"
    }
}

class SyncBalancesTest {

    private lateinit var localStore: FakeLocalStore
    private lateinit var syncBalances: SyncBalances

    @BeforeEach
    fun setUp() {
        localStore = FakeLocalStore()
        syncBalances = SyncBalances(localStore)
    }

    @Test
    fun stores_the_fetched_balances() {
        syncBalances.execute()

        assertThat(localStore.readRawJson()).isEqualTo(REMOTE_JSON)
    }

    companion object {
        private const val REMOTE_JSON = "[{\"id\":\"ACC-1\",\"balance\":100}]"
    }
}

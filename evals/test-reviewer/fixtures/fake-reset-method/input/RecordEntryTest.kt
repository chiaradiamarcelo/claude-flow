class RecordEntryTest {

    private val ledger = FakeLedgerRepository()
    private lateinit var recordEntry: RecordEntry

    @BeforeEach
    fun setUp() {
        ledger.reset()
        recordEntry = RecordEntry(ledger)
    }

    @Test
    fun appends_the_entry_to_the_ledger() {
        recordEntry.execute(LedgerEntry("E-1", amount = 50))

        assertThat(ledger.entries()).containsExactly(LedgerEntry("E-1", amount = 50))
    }
}

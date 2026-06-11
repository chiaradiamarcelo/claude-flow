class SettlementJobTest {

    private lateinit var transfers: FakeTransferRepository
    private lateinit var settlementJob: SettlementJob

    @BeforeEach
    fun setUp() {
        transfers = FakeTransferRepository()
        settlementJob = SettlementJob(transfers)
    }

    @Test
    fun propagates_the_error_when_the_pending_transfers_sql_query_throws() {
        transfers.failWith(QueryFailure("pending_transfers"))

        val result = settlementJob.execute()

        assertThat(result).isEqualTo(SettlementResult.Failed)
    }
}

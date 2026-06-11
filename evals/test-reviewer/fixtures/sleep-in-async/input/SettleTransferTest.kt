class SettleTransferTest {

    private lateinit var transfers: FakeTransferRepository
    private lateinit var settleTransfer: SettleTransfer

    @BeforeEach
    fun setUp() {
        transfers = FakeTransferRepository()
        settleTransfer = SettleTransfer(transfers)
    }

    @Test
    fun marks_the_transfer_as_settled() {
        transfers.save(Transfer(TRANSFER_ID, amount = 100))

        settleTransfer.executeAsync(TRANSFER_ID)
        Thread.sleep(1000)

        assertThat(transfers.byId(TRANSFER_ID).status).isEqualTo(SETTLED)
    }

    companion object {
        private const val TRANSFER_ID = "T-1"
    }
}

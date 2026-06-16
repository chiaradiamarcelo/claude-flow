class TransferReceiptTest {

    private lateinit var transfers: FakeTransferRepository
    private lateinit var issueReceipt: IssueReceipt

    @BeforeEach
    fun setUp() {
        transfers = FakeTransferRepository()
        issueReceipt = IssueReceipt(transfers)
    }

    @Test
    fun formats_the_amount_in_dollars() {
        val formatter = ReceiptFormatter(Clock.fixed(INSTANT, ZoneOffset.UTC), Locale.US, "USD")

        val receipt = formatter.format(Transfer("T-1", 100))

        assertThat(receipt.amount).isEqualTo("$100.00")
    }

    @Test
    fun formats_the_date_in_iso() {
        val formatter = ReceiptFormatter(Clock.fixed(INSTANT, ZoneOffset.UTC), Locale.US, "USD")

        val receipt = formatter.format(Transfer("T-1", 100))

        assertThat(receipt.date).isEqualTo("2024-01-15")
    }

    @Test
    fun includes_the_transfer_id() {
        val formatter = ReceiptFormatter(Clock.fixed(INSTANT, ZoneOffset.UTC), Locale.US, "USD")

        val receipt = formatter.format(Transfer("T-1", 100))

        assertThat(receipt.reference).isEqualTo("T-1")
    }

    companion object {
        private val INSTANT = Instant.parse("2024-01-15T00:00:00Z")
    }
}

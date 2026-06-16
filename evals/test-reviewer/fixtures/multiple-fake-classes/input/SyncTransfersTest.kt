class SyncTransfersTest {

    private lateinit var syncTransfers: SyncTransfers

    @Test
    fun reports_a_failure_when_the_remote_throws() {
        val remote = ThrowingTransferRemote()
        syncTransfers = SyncTransfers(remote)

        val result = syncTransfers.execute()

        assertThat(result).isEqualTo(SyncResult.Failed)
    }

    @Test
    fun reports_a_partial_when_the_remote_times_out() {
        val remote = TimingOutTransferRemote()
        syncTransfers = SyncTransfers(remote)

        val result = syncTransfers.execute()

        assertThat(result).isEqualTo(SyncResult.Partial)
    }
}

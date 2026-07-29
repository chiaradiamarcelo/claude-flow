package example

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class UserReportQueryTest {

    private val query = FakeUserReportQuery()

    @Test
    fun returns_only_active_users() {
        // BATCH_SIZE is 100 — seed 150 rows so the query spans two fetch batches
        seed(
            (1..149).map { row(userId = it.toLong(), active = true) } +
                row(userId = 150, active = false),
        )

        val report = query.activeUsers()

        assertThat(report).hasSize(149)
    }
}

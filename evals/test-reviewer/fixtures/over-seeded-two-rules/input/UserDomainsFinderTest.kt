package example

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class UserDomainsFinderTest {

    private val finder = FakeUserDomainsFinder()

    @Test
    fun returns_distinct_user_ids_of_users_with_non_deleted_domains() {
        seed(listOf(
            row(USER_A, deletionRequestedAt = null),
            row(USER_A, deletionRequestedAt = null),
            row(USER_A, deletionRequestedAt = null),
            row(USER_B, deletionRequestedAt = null),
        ))

        val userIds = finder.findAll()

        assertThat(userIds).hasSize(2)
        assertThat(userIds).containsExactlyInAnyOrder(USER_A, USER_B)
    }
}

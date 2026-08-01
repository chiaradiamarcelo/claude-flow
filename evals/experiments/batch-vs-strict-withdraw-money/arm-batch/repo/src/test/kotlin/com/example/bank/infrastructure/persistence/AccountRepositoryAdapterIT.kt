package com.example.bank.infrastructure.persistence

import com.example.bank.domain.models.account.AccountRepository
import com.example.bank.domain.models.account.AccountRepositoryContractTest
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest

/**
 * The JPA realization of the [AccountRepository] contract. The schema comes from
 * `db/schema.sql` and Hibernate only validates against it, so mapping drift reddens here.
 */
@DataJpaTest(
    properties = [
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.sql.init.mode=always",
        "spring.sql.init.schema-locations=classpath:db/schema.sql",
    ],
)
class AccountRepositoryAdapterIT : AccountRepositoryContractTest() {

    @Autowired
    private lateinit var accountJpaRepository: AccountJpaRepository

    override fun newRepository(): AccountRepository = AccountRepositoryAdapter(accountJpaRepository)
}

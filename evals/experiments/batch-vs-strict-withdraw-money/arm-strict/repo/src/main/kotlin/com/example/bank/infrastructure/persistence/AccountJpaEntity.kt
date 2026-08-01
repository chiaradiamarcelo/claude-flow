package com.example.bank.infrastructure.persistence

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.math.BigDecimal

@Entity
@Table(name = "accounts")
class AccountJpaEntity(

    @Id
    @Column(name = "account_id")
    var accountId: String = "",

    @Column(name = "balance", nullable = false)
    var balance: BigDecimal = BigDecimal.ZERO,
)

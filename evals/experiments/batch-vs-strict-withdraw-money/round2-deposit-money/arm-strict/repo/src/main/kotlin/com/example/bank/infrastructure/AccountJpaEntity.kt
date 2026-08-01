package com.example.bank.infrastructure

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.math.BigDecimal

@Entity
@Table(name = "account")
class AccountJpaEntity(

    @Id
    @Column(name = "account_id", nullable = false)
    var accountId: String = "",

    @Column(name = "balance", nullable = false)
    var balance: BigDecimal = BigDecimal.ZERO,
)

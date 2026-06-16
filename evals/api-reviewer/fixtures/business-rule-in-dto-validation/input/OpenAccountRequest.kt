package banking.api.dto

import jakarta.validation.constraints.Min
import jakarta.validation.constraints.NotBlank
import jakarta.validation.constraints.Pattern

data class OpenAccountRequest(
    @field:NotBlank
    val ownerId: String,

    @field:Min(value = 10_000, message = "minimum opening balance is 100.00")
    val initialBalanceCents: Long,

    @field:Pattern(regexp = "^(SAVINGS|CHECKING)$", message = "unsupported account type")
    val accountType: String,
)

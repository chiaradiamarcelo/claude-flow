package banking.api

import banking.api.dto.StatementResponse
import banking.application.GenerateStatementUseCase
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PathVariable
import org.springframework.web.bind.annotation.RestController

@RestController
class AccountStatementController(
    private val generateStatement: GenerateStatementUseCase,
) {

    @GetMapping("/accounts/{id}/statements")
    fun statement(@PathVariable id: String): StatementResponse {
        val statement = generateStatement.createAndPersist(id)
        return StatementResponse(statement.id, statement.pdfUrl)
    }
}

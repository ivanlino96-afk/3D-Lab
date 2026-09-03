# Matriz de trazabilidad

Fecha de ejecución: 2026-09-03. Resultado del conjunto: 116 pruebas aprobadas.

Las rutas se expresan desde `backend/tests/`. Cada fila enlaza el criterio, todos sus RF, la tarea de validación y evidencia de éxito y error ejecutada.

| CA | RF | Tareas | Prueba de éxito | Prueba de error o límite |
|---|---|---|---|---|
| CA-01 | RF-01 | T017–T021 | `e2e/test_service_catalog.py::test_catalog_displays_published_services_and_quote_action` | `::test_catalog_displays_a_recoverable_error_in_spanish` |
| CA-02 | RF-02–RF-04 | T022, T027, T030 | `e2e/test_material_guide.py::test_filters_materials_and_explains_the_ranking` | `::test_shows_empty_state_and_clear_action_when_there_are_no_matches` |
| CA-03 | RF-03 | T022, T025, T030 | `unit/materials/test_rank_materials.py::test_ranks_by_matches_then_availability_then_cost` | `::test_excludes_unpublished_and_honors_strict_cost_and_availability_filters` |
| CA-04 | RF-05 | T023, T028, T030 | `e2e/test_material_guide.py::test_compares_materials_with_consistent_units_and_missing_values` | `unit/materials/test_material_details.py::test_property_without_value_is_explicitly_unavailable` |
| CA-05 | RF-06, RF-07 | T023, T028, T030 | `e2e/test_material_guide.py::test_detail_only_displays_current_certification_evidence` | `e2e/test_admin_materials.py::test_expired_certification_is_not_claimed_on_a_published_detail` |
| CA-06 | RF-08 | T029, T030 | `e2e/test_material_guide.py::test_selected_published_material_is_forwarded_to_quote` | `::test_archived_selection_is_removed_with_a_spanish_message` |
| CA-07 | RF-09 | T031, T040, T041 | `unit/customers/test_contact_validation.py::test_accepts_contact_without_account_and_normalizes_email` | `::test_rejects_invalid_contact_with_spanish_field_error` |
| CA-08 | RF-10 | T032, T035, T037 | `unit/quotes/test_upload_session.py::test_accepts_twenty_files_with_exact_total_limit` | `::test_rejects_only_the_twenty_first_file`, `::test_rejects_file_that_would_exceed_total_size` |
| CA-09 | RF-10, RF-11 | T032, T036, T037 | `unit/quotes/test_upload_session.py::test_validates_ascii_and_binary_stl_independently` | `::test_invalid_file_does_not_remove_valid_files` |
| CA-10 | RF-12, RF-13 | T032, T037, T041 | `unit/quotes/test_upload_session.py::test_can_remove_and_replace_before_submission` | `::test_pending_upload_blocks_submission_but_keeps_completed_files` |
| CA-11 | RF-14–RF-16 | T033, T038, T039, T042, T044 | `integration/test_quote_lifecycle.py::test_quote_is_idempotent_and_keeps_customer_history_and_contact_snapshots` | `::test_data_change_requires_verified_associated_email` |
| CA-12 | RF-17, RF-18 | T043, T044 | `integration/test_quote_lifecycle.py::test_expiration_deletes_private_stl_but_keeps_metadata` | `security/test_private_access.py::test_valid_admin_still_cannot_download_expired_or_unknown_file` |
| CA-13 | RF-19, RF-20 | T033, T039, T065, T071 | `e2e/test_quote_submission.py::test_visitor_uploads_stl_and_confirms_quote_once` | `integration/test_notification_delivery.py::test_three_provider_failures_do_not_revert_quote_and_are_exposed` |
| CA-14 | RF-21, RF-22 | T051, T065–T071 | `integration/test_notification_delivery.py::test_notification_is_deduplicated_rendered_in_spanish_and_delivered` | `::test_three_provider_failures_do_not_revert_quote_and_are_exposed` |
| CA-15 | RF-23 | T045, T049, T054, T079 | `e2e/test_admin_quote_management.py::test_private_panel_rejects_anonymous_and_accepts_only_valid_credentials` | `security/test_private_access.py::test_anonymous_and_forged_references_cannot_read_private_data` |
| CA-16 | RF-24–RF-26 | T047, T052, T053, T057, T079 | `e2e/test_admin_quote_management.py::test_filters_detail_and_private_download` | `security/test_private_access.py::test_valid_admin_still_cannot_download_expired_or_unknown_file` |
| CA-17 | RF-27 | T046, T050, T051, T057 | `unit/quotes/test_status_transitions.py::test_allowed_transitions_create_an_append_only_event` | `::test_skipped_repeated_and_terminal_transitions_are_rejected` |
| CA-18 | RF-28, RF-29 | T046, T051, T057, T076 | `e2e/test_admin_quote_management.py::test_status_cycle_records_sale_history_notifications_and_terminal_rule` | `::test_canceled_sale_keeps_its_sale_timestamp_but_is_no_longer_effective` |
| CA-19 | RF-31 | T058–T064 | `e2e/test_admin_materials.py::test_complete_material_can_be_published_and_appears_publicly` | `::test_missing_fields_and_expired_evidence_block_publication` |
| CA-20 | RF-32 | T059, T061, T064 | `e2e/test_admin_materials.py::test_archiving_keeps_historical_quote_reference_and_removes_public_selection` | La misma prueba verifica que ya no se ofrece en nuevas solicitudes. |
| CA-21 | RF-33 | T072–T076, T080 | `integration/test_commercial_metrics.py::test_metrics_derive_sales_and_cancellations_from_real_history` | `unit/reporting/test_calculate_metrics.py::test_invalid_period_is_rejected_in_spanish` |
| CA-22 | RF-34, RF-35 | T013, T077, T078 | `e2e/test_quote_submission.py::test_visitor_uploads_stl_and_confirms_quote_once` | `e2e/test_material_guide.py::test_repository_failure_has_recoverable_spanish_state` |
| CA-23 | RF-09, RF-10 | T031–T033, T040, T041 | `e2e/test_quote_submission.py::test_visitor_uploads_stl_and_confirms_quote_once` | `::test_invalid_contact_keeps_request_open_and_explains_error`, `unit/quotes/test_confirm_quote.py::test_rejects_submission_without_valid_stl_and_rolls_back` |
| CA-24 | RF-36 | T032, T037, T041 | `unit/quotes/test_upload_session.py::test_invalid_file_does_not_remove_valid_files` | `::test_pending_upload_blocks_submission_but_keeps_completed_files` |
| CA-25 | RF-38 | T033, T039, T041 | `unit/quotes/test_confirm_quote.py::test_confirms_once_and_creates_customer_files_audit_and_notifications` | `::test_second_activation_returns_existing_quote_without_duplicates` |
| CA-26 | RF-23 | T045, T049, T054, T057 | `unit/administration/test_admin_session.py::test_valid_credentials_create_a_protected_session_and_logout` | `::test_invalid_credentials_always_return_the_same_message` |
| CA-27 | RF-24, RF-30 | T047, T052, T056, T057, T080 | `e2e/test_admin_quote_management.py::test_filters_detail_and_private_download` | `unit/administration/test_quote_queries.py::test_empty_filters_and_invalid_pages_use_safe_defaults` |
| CA-28 | RF-07, RF-31 | T058, T060, T064 | `unit/materials/test_material_details.py::test_certification_is_public_only_with_current_evidence` | `unit/materials/test_manage_material.py::test_expired_or_unsupported_certification_cannot_be_published` |
| CA-29 | RF-32, RF-37 | T030, T059, T064 | `e2e/test_material_guide.py::test_shows_empty_state_and_clear_action_when_there_are_no_matches` | `::test_archived_selection_is_removed_with_a_spanish_message` |
| CA-30 | RF-22 | T066, T069–T071 | `unit/notifications/test_deliver_notification.py::test_failure_is_scheduled_and_a_later_attempt_can_recover` | `::test_third_failure_is_not_delivered_and_never_attempted_a_fourth_time` |
| CA-31 | RF-15, RF-16 | T038, T042, T044 | `integration/test_quote_lifecycle.py::test_quote_is_idempotent_and_keeps_customer_history_and_contact_snapshots` | `::test_data_change_requires_verified_associated_email` |
| CA-32 | RF-14, RF-39 | T033, T039 | `unit/quotes/test_confirm_quote.py::test_confirms_once_and_creates_customer_files_audit_and_notifications` | `::test_reference_collision_generates_another_reference` |

## Requisitos no funcionales

| RNF | Evidencia | Estado |
|---|---|---|
| RNF-01 | `evidence/usability.md` | Pendiente de 12 participantes reales |
| RNF-02–RNF-04 | `performance/test_capacity.py` y `evidence/performance.md` | Aprobado localmente; requiere telemetría de producción para RNF-02 |
| RNF-05–RNF-06 | `frontend/src/styles/responsive.css`, prueba de navegador en 390, 768 y 1440 px | Aprobado |
| RNF-07 | `security/test_private_access.py` | Aprobado |
| RNF-08 | `architecture/test_dependencies.py` | Aprobado |

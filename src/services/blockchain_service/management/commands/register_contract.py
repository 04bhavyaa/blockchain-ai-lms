from django.core.management.base import BaseCommand, CommandError
import json
import os

from src.services.blockchain_service.models import SmartContractConfig


class Command(BaseCommand):
    help = 'Register a deployed contract into SmartContractConfig from a Hardhat artifact'

    def add_arguments(self, parser):
        parser.add_argument('--artifact', type=str, required=True, help='Path to compiled artifact JSON (Hardhat artifact)')
        parser.add_argument('--contract-type', type=str, required=True, help='Contract type key (e.g., ap2, token, certificate)')
        parser.add_argument('--address', type=str, required=True, help='Deployed contract address')
        parser.add_argument('--block-number', type=int, default=0, help='Block number of deployment (optional)')
        parser.add_argument('--network', type=str, default='localhost', help='Network name')

    def handle(self, *args, **options):
        artifact_path = options['artifact']
        contract_type = options['contract_type']
        address = options['address']
        block_number = options['block_number']
        network = options['network']

        if not os.path.exists(artifact_path):
            raise CommandError(f'Artifact not found: {artifact_path}')

        with open(artifact_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        abi = data.get('abi') or data
        deployment_hash = data.get('deployedBytecode', '')[:255]

        obj, created = SmartContractConfig.objects.update_or_create(
            contract_type=contract_type,
            defaults={
                'contract_address': address,
                'contract_abi': abi,
                'deployment_hash': deployment_hash,
                'block_number': block_number,
                'network': network,
                'is_active': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created SmartContractConfig for {contract_type} @ {address}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated SmartContractConfig for {contract_type} @ {address}'))

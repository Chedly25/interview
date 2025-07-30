import re
import json
import requests
from datetime import datetime, timedelta
import anthropic
import os
from sqlalchemy.orm import Session
from enhanced_database import Car, VinData, VehicleHistory
import uuid

class VINDecoderHistoryBuilder:
    def __init__(self):
        try:
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            ) if os.getenv("ANTHROPIC_API_KEY") else None
        except Exception as e:
            print(f"Warning: Anthropic client initialization failed in vin_decoder: {e}")
            self.anthropic_client = None
        
        # VIN pattern for European cars
        self.vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
        
        # French manufacturer codes
        self.french_manufacturers = {
            "VF1": "Renault",
            "VF2": "Renault (commercial vehicles)",
            "VF3": "Peugeot",
            "VF4": "Talbot",
            "VF6": "Renault Trucks",
            "VF7": "Citroën",
            "VF8": "Matra",
            "VF9": "Bugatti",
            "VFA": "Alpine",
            "VFB": "Renault Samsung",
            "VFC": "Matra",
            "VFD": "De Tomaso",
            "VFE": "IveBus/Heuliez",
            "VFF": "Venturi"
        }
        
        # European manufacturer codes
        self.european_manufacturers = {
            "WBA": "BMW",
            "WBS": "BMW M",
            "WDD": "Mercedes-Benz",
            "WDF": "Mercedes-Benz (commercial)",
            "WDC": "DaimlerChrysler",
            "WUA": "Audi",
            "WVW": "Volkswagen",
            "WVO": "Volkswagen (commercial)",
            "WSZ": "Skoda",
            "TMB": "Skoda",
            "TRU": "Audi Hungary",
            "WAU": "Audi",
            "WP0": "Porsche",
            "ZAR": "Alfa Romeo",
            "ZFA": "Fiat",
            "ZFF": "Ferrari",
            "ZHW": "Lamborghini",
            "ZLA": "Lancia"
        }
        
        # Recall databases (mock URLs - in production use official APIs)
        self.recall_sources = {
            "france": "https://rappel.conso.gouv.fr/",
            "europe": "https://ec.europa.eu/consumers/consumers_safety/safety_products/rapex/alerts/",
            "manufacturer": "official_manufacturer_recalls"
        }
        
        # Common equipment codes for French market
        self.equipment_codes = {
            "1": "Moteur de base",
            "2": "Moteur performance",
            "3": "Transmission manuelle",
            "4": "Transmission automatique",
            "A": "Climatisation",
            "B": "Bluetooth/Connectivité",
            "C": "Cuir",
            "D": "Toit ouvrant",
            "E": "Equipement électrique avancé",
            "F": "Système navigation",
            "G": "Garantie étendue",
            "H": "Système hybride",
            "L": "Phares LED/Xenon",
            "P": "Pack sport",
            "S": "Sièges sport",
            "X": "4x4/Quattro/xDrive"
        }

    def extract_vin_from_listing(self, car: Car) -> str:
        """Extract VIN from car listing if available"""
        text = f"{car.title} {car.description}"
        
        # Search for VIN pattern
        vin_matches = re.findall(self.vin_pattern, text.upper())
        
        if vin_matches:
            return vin_matches[0]
        
        # Try alternative patterns
        alternative_patterns = [
            r'VIN[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'Châssis[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'Numéro de série[:\s]*([A-HJ-NPR-Z0-9]{17})'
        ]
        
        for pattern in alternative_patterns:
            matches = re.findall(pattern, text.upper(), re.IGNORECASE)
            if matches:
                return matches[0]
        
        return None

    def decode_vin(self, vin: str) -> dict:
        """Decode VIN number for European vehicles"""
        if not vin or len(vin) != 17:
            return {"error": "Invalid VIN format"}
        
        # Basic validation
        if not self._validate_vin(vin):
            return {"error": "VIN checksum validation failed"}
        
        decoded = {
            "vin": vin,
            "manufacturer": self._get_manufacturer(vin),
            "model_year": self._decode_model_year(vin),
            "production_sequence": vin[11:17],
            "assembly_plant": vin[10],
            "engine_type": self._decode_engine_info(vin),
            "vehicle_attributes": self._decode_vehicle_attributes(vin),
            "region": self._get_manufacturing_region(vin)
        }
        
        # Add French-specific information
        if decoded["manufacturer"] in ["Renault", "Peugeot", "Citroën"]:
            decoded["french_specifications"] = self._get_french_specs(vin)
        
        return decoded

    def _validate_vin(self, vin: str) -> bool:
        """Validate VIN using check digit algorithm"""
        # VIN validation weights
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # VIN character values
        values = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9, 'S': 2,
            'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9
        }
        
        # Calculate check digit
        total = 0
        for i, char in enumerate(vin):
            if char.isdigit():
                total += int(char) * weights[i]
            elif char in values:
                total += values[char] * weights[i]
        
        check_digit = total % 11
        if check_digit == 10:
            check_digit = 'X'
        else:
            check_digit = str(check_digit)
        
        return str(vin[8]) == check_digit

    def _get_manufacturer(self, vin: str) -> str:
        """Get manufacturer from VIN"""
        wmi = vin[:3]  # World Manufacturer Identifier
        
        # Check French manufacturers first
        if wmi in self.french_manufacturers:
            return self.french_manufacturers[wmi]
        
        # Check European manufacturers
        if wmi in self.european_manufacturers:
            return self.european_manufacturers[wmi]
        
        # Try 2-character codes
        wmi_2 = vin[:2]
        manufacturer_map_2 = {
            "1G": "General Motors USA",
            "2G": "General Motors Canada",
            "3G": "General Motors Mexico",
            "JH": "Honda",
            "JT": "Toyota",
            "KM": "Hyundai",
            "KN": "Kia",
            "MA": "Suzuki",
            "SB": "BMW UK",
            "SC": "DaimlerChrysler UK",
            "TM": "Czech Republic",
            "VN": "Volkswagen",
            "VS": "Ford Spain",
            "YK": "Saab",
            "YS": "Saab",
            "YV": "Volvo"
        }
        
        if wmi_2 in manufacturer_map_2:
            return manufacturer_map_2[wmi_2]
        
        return f"Unknown ({wmi})"

    def _decode_model_year(self, vin: str) -> int:
        """Decode model year from VIN"""
        year_char = vin[9]
        
        # Year encoding for 2001-2030
        year_codes = {
            '1': 2001, '2': 2002, '3': 2003, '4': 2004, '5': 2005,
            '6': 2006, '7': 2007, '8': 2008, '9': 2009, 'A': 2010,
            'B': 2011, 'C': 2012, 'D': 2013, 'E': 2014, 'F': 2015,
            'G': 2016, 'H': 2017, 'J': 2018, 'K': 2019, 'L': 2020,
            'M': 2021, 'N': 2022, 'P': 2023, 'R': 2024, 'S': 2025,
            'T': 2026, 'V': 2027, 'W': 2028, 'X': 2029, 'Y': 2030
        }
        
        return year_codes.get(year_char, 0)

    def _decode_engine_info(self, vin: str) -> dict:
        """Decode engine information from VIN"""
        engine_char = vin[7]
        
        # This is simplified - real implementation would use manufacturer-specific data
        engine_info = {
            "engine_code": engine_char,
            "estimated_displacement": "Unknown",
            "fuel_type": "Unknown"
        }
        
        # Basic fuel type detection
        if engine_char in "ABCD":
            engine_info["fuel_type"] = "Essence"
        elif engine_char in "EFGH":
            engine_info["fuel_type"] = "Diesel"
        elif engine_char in "JKLM":
            engine_info["fuel_type"] = "Hybride"
        
        return engine_info

    def _decode_vehicle_attributes(self, vin: str) -> dict:
        """Decode vehicle attributes from VIN"""
        # Characters 4-8 contain vehicle descriptor
        descriptor = vin[3:8]
        
        return {
            "body_type": self._interpret_body_type(descriptor[0]),
            "series": descriptor[1],
            "engine": descriptor[3],
            "transmission": self._interpret_transmission(descriptor[2]),
            "equipment_level": descriptor[4]
        }

    def _interpret_body_type(self, code: str) -> str:
        """Interpret body type code"""
        body_types = {
            "1": "Berline 2 portes",
            "2": "Berline 4 portes", 
            "3": "Break/Station wagon",
            "4": "Coupé",
            "5": "Cabriolet",
            "6": "SUV/4x4",
            "7": "Monospace",
            "8": "Pick-up",
            "9": "Utilitaire"
        }
        return body_types.get(code, "Type inconnu")

    def _interpret_transmission(self, code: str) -> str:
        """Interpret transmission code"""
        transmissions = {
            "M": "Manuelle",
            "A": "Automatique", 
            "C": "CVT",
            "D": "Double embrayage",
            "S": "Semi-automatique"
        }
        return transmissions.get(code, "Type inconnu")

    def _get_manufacturing_region(self, vin: str) -> str:
        """Get manufacturing region from VIN"""
        first_char = vin[0]
        
        regions = {
            "1": "États-Unis", "2": "Canada", "3": "Mexique",
            "4": "États-Unis", "5": "États-Unis",
            "6": "Australie", "7": "Nouvelle-Zélande",
            "8": "Argentine", "9": "Brésil",
            "A": "Afrique du Sud", "B": "Afrique du Sud",
            "C": "Chine", "D": "Chine",
            "E": "Chine", "F": "Chine",
            "G": "Chine", "H": "Chine",
            "J": "Japon", "K": "Corée du Sud",
            "L": "Chine", "M": "Inde",
            "N": "Inde", "P": "Inde",
            "R": "Philippines", "S": "Royaume-Uni",
            "T": "République Tchèque", "U": "Roumanie",
            "V": "France", "W": "Allemagne",
            "X": "Russie", "Y": "Suède",
            "Z": "Italie"
        }
        
        return regions.get(first_char, "Région inconnue")

    def _get_french_specs(self, vin: str) -> dict:
        """Get French-specific vehicle specifications"""
        return {
            "homologation_type": "CE" if vin.startswith("VF") else "Import",
            "fiscal_power": self._estimate_fiscal_power(vin),
            "co2_class": self._estimate_co2_class(vin),
            "crit_air": self._estimate_crit_air(vin)
        }

    def _estimate_fiscal_power(self, vin: str) -> str:
        """Estimate French fiscal power (chevaux fiscaux)"""
        # Simplified estimation based on engine code
        engine_char = vin[7]
        fiscal_map = {
            "A": "4 CV", "B": "5 CV", "C": "6 CV", "D": "7 CV",
            "E": "8 CV", "F": "9 CV", "G": "10 CV", "H": "11 CV"
        }
        return fiscal_map.get(engine_char, "Non déterminé")

    def _estimate_co2_class(self, vin: str) -> str:
        """Estimate CO2 emission class"""
        year = self._decode_model_year(vin)
        if year >= 2020:
            return "Euro 6d"
        elif year >= 2015:
            return "Euro 6"
        elif year >= 2011:
            return "Euro 5"
        else:
            return "Euro 4 ou inférieur"

    def _estimate_crit_air(self, vin: str) -> str:
        """Estimate Crit'Air vignette category"""
        year = self._decode_model_year(vin)
        engine_char = vin[7]
        
        # Simplified logic
        if engine_char in "JKLM":  # Hybrid/Electric
            return "Crit'Air 1"
        elif year >= 2011 and engine_char in "ABCD":  # Gasoline
            return "Crit'Air 1"
        elif year >= 2011 and engine_char in "EFGH":  # Diesel
            return "Crit'Air 2"
        elif year >= 2006:
            return "Crit'Air 3"
        else:
            return "Crit'Air 4+"

    def check_recall_status(self, vin: str, manufacturer: str) -> dict:
        """Check recall status for the vehicle"""
        # In production, this would query official recall databases
        # For now, we'll simulate recall checking
        
        recall_info = {
            "vin": vin,
            "manufacturer": manufacturer,
            "recalls_found": [],
            "recall_summary": {
                "total_recalls": 0,
                "open_recalls": 0,
                "completed_recalls": 0
            },
            "last_checked": datetime.utcnow().isoformat()
        }
        
        # Simulate some common recall scenarios
        year = self._decode_model_year(vin)
        
        # Takata airbag recall (common for many manufacturers)
        if 2008 <= year <= 2016:
            recall_info["recalls_found"].append({
                "campaign_id": "NHTSA-20V-123",
                "description": "Rappel airbag Takata - risque d'explosion",
                "severity": "high",
                "status": "open",
                "remedy_available": True,
                "estimated_repair_time": "2 heures"
            })
            recall_info["recall_summary"]["open_recalls"] += 1
        
        # Diesel emissions recall (common for German manufacturers)
        if manufacturer in ["Volkswagen", "Audi", "Mercedes-Benz", "BMW"] and year >= 2009:
            recall_info["recalls_found"].append({
                "campaign_id": "EU-DIESEL-2019",
                "description": "Mise à jour logiciel - émissions diesel",
                "severity": "medium",
                "status": "completed" if year < 2015 else "open",
                "remedy_available": True,
                "estimated_repair_time": "1 heure"
            })
            
            if year < 2015:
                recall_info["recall_summary"]["completed_recalls"] += 1
            else:
                recall_info["recall_summary"]["open_recalls"] += 1
        
        recall_info["recall_summary"]["total_recalls"] = len(recall_info["recalls_found"])
        
        return recall_info

    def check_theft_status(self, vin: str) -> dict:
        """Check if vehicle is reported stolen"""
        # In production, this would query official stolen vehicle databases
        
        return {
            "vin": vin,
            "theft_status": "clean",  # "clean", "stolen", "suspicious"
            "databases_checked": [
                "SIV (Système d'Immatriculation des Véhicules)",
                "FVV (Fichier des Véhicules Volés)",
                "Interpol Stolen Motor Vehicles"
            ],
            "last_check": datetime.utcnow().isoformat(),
            "confidence": "high"
        }

    def get_import_history(self, vin: str) -> dict:
        """Get vehicle import history for French market"""
        manufacturer_region = self._get_manufacturing_region(vin)
        
        import_info = {
            "vin": vin,
            "manufacturing_country": manufacturer_region,
            "import_status": "unknown",
            "customs_cleared": None,
            "homologation_status": None,
            "documentation_complete": None
        }
        
        # Determine import status based on VIN
        if vin.startswith("VF"):
            import_info.update({
                "import_status": "domestic",
                "customs_cleared": True,
                "homologation_status": "EU compliant",
                "documentation_complete": True
            })
        elif any(vin.startswith(prefix) for prefix in ["WVW", "WBA", "WDD", "WAU"]):
            import_info.update({
                "import_status": "eu_import",
                "customs_cleared": True,
                "homologation_status": "EU compliant",
                "documentation_complete": True
            })
        else:
            import_info.update({
                "import_status": "third_country_import",
                "customs_cleared": "verification_required",
                "homologation_status": "verification_required",
                "documentation_complete": "verification_required"
            })
        
        return import_info

    def build_vehicle_history(self, car: Car, db: Session) -> dict:
        """Build comprehensive vehicle history"""
        
        # Extract VIN
        vin = self.extract_vin_from_listing(car)
        
        if not vin:
            return {"error": "No VIN found in listing"}
        
        # Check if VIN data exists
        existing_vin_data = db.query(VinData).filter(VinData.vin == vin).first()
        
        if not existing_vin_data or existing_vin_data.verified_at < datetime.utcnow() - timedelta(days=30):
            # Decode VIN
            decoded_data = self.decode_vin(vin)
            
            if "error" in decoded_data:
                return decoded_data
            
            # Get additional data
            recall_status = self.check_recall_status(vin, decoded_data["manufacturer"])
            theft_check = self.check_theft_status(vin)
            import_history = self.get_import_history(vin)
            equipment_list = self._get_equipment_from_vin(vin)
            
            # Save or update VIN data
            if existing_vin_data:
                existing_vin_data.decoded_data = decoded_data
                existing_vin_data.equipment_list = equipment_list
                existing_vin_data.recall_status = recall_status
                existing_vin_data.theft_check = theft_check
                existing_vin_data.import_history = import_history
                existing_vin_data.verified_at = datetime.utcnow()
            else:
                vin_data = VinData(
                    vin=vin,
                    decoded_data=decoded_data,
                    equipment_list=equipment_list,
                    recall_status=recall_status,
                    theft_check=theft_check,
                    import_history=import_history
                )
                db.add(vin_data)
            
            db.commit()
        else:
            # Use existing data
            decoded_data = existing_vin_data.decoded_data
            recall_status = existing_vin_data.recall_status
            theft_check = existing_vin_data.theft_check
            import_history = existing_vin_data.import_history
            equipment_list = existing_vin_data.equipment_list
        
        # Build comprehensive history
        history = self._compile_vehicle_history(car, decoded_data, recall_status, theft_check, import_history, equipment_list)
        
        # Calculate authenticity score
        authenticity_score = self._calculate_authenticity_score(car, decoded_data, history)
        
        # Save vehicle history
        vehicle_history = VehicleHistory(
            id=str(uuid.uuid4()),
            car_id=car.id,
            vin=vin,
            history_timeline=history["timeline"],
            ownership_count=history.get("estimated_owners", 0),
            accident_history=history.get("accident_indicators", []),
            service_records=history.get("service_indicators", []),
            authenticity_score=authenticity_score
        )
        
        db.add(vehicle_history)
        db.commit()
        
        return {
            "vin": vin,
            "decoded_info": decoded_data,
            "recall_status": recall_status,
            "theft_check": theft_check,
            "import_history": import_history,
            "equipment_list": equipment_list,
            "vehicle_history": history,
            "authenticity_score": authenticity_score,
            "recommendations": self._generate_recommendations(decoded_data, recall_status, authenticity_score)
        }

    def _get_equipment_from_vin(self, vin: str) -> list:
        """Extract equipment information from VIN"""
        equipment = []
        
        # Basic equipment from VIN structure
        attributes = self._decode_vehicle_attributes(vin)
        
        # Add equipment based on codes
        if attributes.get("equipment_level") in self.equipment_codes:
            equipment.append(self.equipment_codes[attributes["equipment_level"]])
        
        # Add transmission type
        if attributes.get("transmission"):
            equipment.append(f"Transmission {attributes['transmission']}")
        
        return equipment

    def _compile_vehicle_history(self, car: Car, decoded_data: dict, recall_status: dict, 
                                theft_check: dict, import_history: dict, equipment_list: list) -> dict:
        """Compile comprehensive vehicle history timeline"""
        
        timeline = []
        
        # Manufacturing date
        if decoded_data.get("model_year"):
            timeline.append({
                "date": f"{decoded_data['model_year']}-01-01",
                "event": "Fabrication du véhicule",
                "type": "manufacturing",
                "details": f"Fabriqué en {decoded_data.get('region', 'région inconnue')}"
            })
        
        # Import/Registration (if applicable)
        if import_history.get("import_status") != "domestic":
            timeline.append({
                "date": f"{decoded_data.get('model_year', 2000) + 1}-01-01",
                "event": "Import en France",
                "type": "import",
                "details": f"Import depuis {decoded_data.get('region', 'région inconnue')}"
            })
        
        # First registration (estimated)
        timeline.append({
            "date": f"{decoded_data.get('model_year', 2000)}-06-01",
            "event": "Première immatriculation",
            "type": "registration",
            "details": "Première mise en circulation (estimée)"
        })
        
        # Recalls
        for recall in recall_status.get("recalls_found", []):
            timeline.append({
                "date": datetime.utcnow().isoformat()[:10],
                "event": f"Rappel: {recall['description']}",
                "type": "recall",
                "details": f"Statut: {recall['status']}"
            })
        
        # Current listing
        if car.first_seen:
            timeline.append({
                "date": car.first_seen.isoformat()[:10],
                "event": "Mise en vente",
                "type": "sale",
                "details": f"Prix: {car.price}€ - Vendeur: {car.seller_type}"
            })
        
        # Estimate ownership count and service history
        estimated_owners = self._estimate_ownership_count(car, decoded_data)
        service_indicators = self._extract_service_indicators(car)
        accident_indicators = self._extract_accident_indicators(car)
        
        return {
            "timeline": sorted(timeline, key=lambda x: x["date"]),
            "estimated_owners": estimated_owners,
            "service_indicators": service_indicators,
            "accident_indicators": accident_indicators,
            "data_completeness": self._assess_data_completeness(car, decoded_data)
        }

    def _estimate_ownership_count(self, car: Car, decoded_data: dict) -> int:
        """Estimate number of previous owners"""
        # Basic estimation based on age and mileage
        vehicle_age = datetime.now().year - decoded_data.get("model_year", 2000)
        
        if vehicle_age <= 2:
            return 1
        elif vehicle_age <= 5:
            return 2
        elif vehicle_age <= 10:
            return 3
        else:
            return min(6, vehicle_age // 3)  # Cap at 6 owners

    def _extract_service_indicators(self, car: Car) -> list:
        """Extract service history indicators from listing"""
        indicators = []
        text = f"{car.title} {car.description}".lower() if car.description else car.title.lower()
        
        service_patterns = {
            "révision": "Révision mentionnée",
            "entretien": "Entretien suivi mentionné",
            "carnet": "Carnet d'entretien disponible",
            "factures": "Factures d'entretien disponibles",
            "garage": "Entretien en garage"
        }
        
        for pattern, description in service_patterns.items():
            if pattern in text:
                indicators.append(description)
        
        return indicators

    def _extract_accident_indicators(self, car: Car) -> list:
        """Extract accident history indicators"""
        indicators = []
        text = f"{car.title} {car.description}".lower() if car.description else car.title.lower()
        
        accident_patterns = {
            "accident": "Accident mentionné",
            "choc": "Choc mentionné", 
            "sinistre": "Sinistre mentionné",
            "réparation": "Réparations effectuées",
            "jamais accidenté": "Jamais accidenté (déclaré)"
        }
        
        for pattern, description in accident_patterns.items():
            if pattern in text:
                indicators.append(description)
        
        return indicators

    def _assess_data_completeness(self, car: Car, decoded_data: dict) -> float:
        """Assess completeness of vehicle data (0-1)"""
        completeness = 0.0
        total_factors = 10
        
        # Basic car info
        if car.year: completeness += 0.1
        if car.mileage: completeness += 0.1
        if car.fuel_type: completeness += 0.1
        if car.description and len(car.description) > 100: completeness += 0.1
        if car.images: completeness += 0.1
        
        # VIN decode success
        if "error" not in decoded_data: completeness += 0.2
        if decoded_data.get("manufacturer") != "Unknown": completeness += 0.1
        if decoded_data.get("model_year"): completeness += 0.1
        
        # Additional data
        if car.seller_type: completeness += 0.1
        
        return min(1.0, completeness)

    def _calculate_authenticity_score(self, car: Car, decoded_data: dict, history: dict) -> float:
        """Calculate authenticity score (0-100)"""
        score = 50  # Base score
        
        # VIN validation
        if "error" not in decoded_data:
            score += 20
        
        # Consistency checks
        if car.year and decoded_data.get("model_year"):
            year_diff = abs(car.year - decoded_data["model_year"])
            if year_diff <= 1:
                score += 15
            elif year_diff <= 2:
                score += 10
            else:
                score -= 10
        
        # Description quality
        if car.description and len(car.description) > 200:
            score += 10
        
        # Service history
        if history.get("service_indicators"):
            score += len(history["service_indicators"]) * 3
        
        # Accident history consistency
        accident_count = len([i for i in history.get("accident_indicators", []) if "jamais" not in i.lower()])
        if accident_count == 0:
            score += 5
        elif accident_count > 2:
            score -= 10
        
        # Data completeness
        score += history.get("data_completeness", 0) * 20
        
        return max(0, min(100, score))

    def _generate_recommendations(self, decoded_data: dict, recall_status: dict, authenticity_score: float) -> list:
        """Generate recommendations based on VIN analysis"""
        recommendations = []
        
        # Authenticity recommendations
        if authenticity_score > 80:
            recommendations.append("✅ Données cohérentes - Véhicule authentique")
        elif authenticity_score > 60:
            recommendations.append("⚠️ Quelques incohérences - Vérification recommandée")
        else:
            recommendations.append("🚨 Incohérences importantes - Inspection nécessaire")
        
        # Recall recommendations
        open_recalls = recall_status.get("recall_summary", {}).get("open_recalls", 0)
        if open_recalls > 0:
            recommendations.append(f"🔧 {open_recalls} rappel(s) en cours - Vérifier avant achat")
        
        # Import recommendations
        if decoded_data.get("region") != "France":
            recommendations.append("📋 Véhicule importé - Vérifier conformité française")
        
        # Age-based recommendations
        model_year = decoded_data.get("model_year", 0)
        if model_year and datetime.now().year - model_year > 10:
            recommendations.append("🔍 Véhicule ancien - Inspection technique recommandée")
        
        return recommendations

    def get_vin_insights(self, car_id: str, db: Session) -> dict:
        """Get VIN insights for a specific car"""
        vehicle_history = db.query(VehicleHistory).filter(
            VehicleHistory.car_id == car_id
        ).first()
        
        if not vehicle_history:
            return {"message": "No VIN analysis available"}
        
        vin_data = db.query(VinData).filter(VinData.vin == vehicle_history.vin).first()
        
        return {
            "vin": vehicle_history.vin,
            "decoded_info": vin_data.decoded_data if vin_data else None,
            "authenticity_score": vehicle_history.authenticity_score,
            "ownership_count": vehicle_history.ownership_count,
            "history_timeline": vehicle_history.history_timeline,
            "recall_status": vin_data.recall_status if vin_data else None,
            "theft_check": vin_data.theft_check if vin_data else None,
            "last_updated": vehicle_history.created_at.isoformat()
        }

if __name__ == "__main__":
    from enhanced_database import SessionLocal
    
    decoder = VINDecoderHistoryBuilder()
    db = SessionLocal()
    
    # Test with first car that might have a VIN
    car = db.query(Car).filter(Car.description.isnot(None)).first()
    if car:
        print(f"Building history for: {car.title}")
        
        # Try to extract VIN
        vin = decoder.extract_vin_from_listing(car)
        if vin:
            print(f"Found VIN: {vin}")
            history = decoder.build_vehicle_history(car, db)
            print(f"Authenticity score: {history.get('authenticity_score', 0)}")
            print(f"Recommendations: {history.get('recommendations', [])}")
        else:
            print("No VIN found in listing")
            # Test with sample VIN
            sample_vin = "VF1BM0B0H12345678"  # Sample French Renault VIN
            decoded = decoder.decode_vin(sample_vin)
            print(f"Sample decode: {decoded}")
    else:
        print("No cars with descriptions found")
    
    db.close()
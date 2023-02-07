from qiskit import *
from .QArithmetic import add, sub, sub_swap
import numpy as np

from qiskit.utils import QuantumInstance
from qiskit.algorithms import IterativeAmplitudeEstimation, EstimationProblem
from qiskit.circuit.library import LinearAmplitudeFunction

from .distribution import Distribution
from .error import QMCError
from .variable import Variable
from .arithmetic import Arithmetic


import warnings
warnings.filterwarnings("ignore")
class QuantumEstimation:
    
    def __init__(
        self,
        qc: QuantumCircuit = None,
    ) -> None:
        if qc == None:
            self.qc = QuantumCircuit()
        else:
            self.qc = qc
    
    def estimate(
        self,
        var: Variable,
        objective: LinearAmplitudeFunction = None,
        
    ):
        self.var = var

        num_uncertainty_qubits = self.var.num_qubits

        qregs = self.qc.qregs

        #arithmetic expectation value
        if objective == None:
            self.plain = True
            slopes = 1 
            low = 0
            high = 1
            offsets = 0
            f_min = 0
            f_max = 1
            c_approx = 0.1 #rescaling factor is important, need to explore which value is better
            
            objective = LinearAmplitudeFunction(
                num_uncertainty_qubits,
                slopes,
                offsets,
                domain=(low, high),
                image=(f_min, f_max),
                rescaling_factor=c_approx,
            )
            
        self.objective = objective
        
        num_qubits = objective.num_qubits
        
        am = QuantumRegister(num_qubits - num_uncertainty_qubits, "am")
        self.qc.add_register(am)
                
        qubits = []
        
        estimated_register = var.get_register()
        
        for i in self.qc._qubits:
            if i.register.name == estimated_register.name:
                qubits.append(i)
        
        for i in self.qc._qubits:
            if i.register.name == am.name:
                qubits.append(i)
                
#         print("qubits:", len(qubits))
        
        self.qc = self.qc.compose(self.objective, qubits)
        
    def calculate(
        self,
        epsilon: float,
        alpha: float,
        plain: bool = False,
        ):
        qregs = self.qc.qregs
        
        qi = QuantumInstance(Aer.get_backend("aer_simulator"), shots = 1000)
        problem = EstimationProblem(
            state_preparation=self.qc,
            objective_qubits=[self.qc.width() - qregs[-1].size],
            post_processing=self.objective.post_processing,
        )
        self.problem = problem
        
        # construct amplitude estimation
        
        ae = IterativeAmplitudeEstimation(epsilon, alpha = alpha, quantum_instance = qi)
        

        # The estimation process will transform the interval into the object interval.          
        import math
        result = ae.estimate(problem)
        
        if plain == True:
            result = result.estimation_processed * (2 ** self.var.num_qubits - 1)

        else:
            result = result.estimation_processed
        
        return result

    def get_qc(self):
        return self.qc